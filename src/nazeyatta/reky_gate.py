from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any

from .evaluator import stable_hash


TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,127}$")
EVIDENCE_STATES = {"VERIFIED", "PRESENT", "STALE", "INVALID", "MISSING", "UNKNOWN"}
DEGRADED_EVIDENCE_STATES = {"STALE", "INVALID", "MISSING", "UNKNOWN"}

OBSERVATION_KEYS = {
    "schema_version",
    "observation_id",
    "classification",
    "task_id",
    "handoff_fingerprint",
    "target_binding",
    "authority_binding",
    "policy_binding",
    "evidence_bindings",
    "observed_by",
    "observed_at",
}


class ObservationGateError(ValueError):
    """Boundary observations cannot be compared safely."""


@dataclass(frozen=True)
class ReKYReason:
    code: str
    detail: str


@dataclass(frozen=True)
class ReKYDecision:
    schema_version: str
    task_id: str
    handoff_fingerprint: str
    before_observation_id: str
    after_observation_id: str
    before_fingerprint: str
    after_fingerprint: str
    outcome: str
    reasons: list[dict[str, str]]
    authority_granted: bool


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObservationGateError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise ObservationGateError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise ObservationGateError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise ObservationGateError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise ObservationGateError(f"{where} must be at most {max_len} characters")
    return value


def _token(value: Any, where: str) -> str:
    token = _string(value, where, max_len=128)
    if not TOKEN_RE.fullmatch(token):
        raise ObservationGateError(f"{where} must be a normalized lowercase token")
    return token


def _timestamp(value: Any, where: str) -> datetime:
    raw = _string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ObservationGateError(f"{where} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise ObservationGateError(f"{where} must include a timezone")
    return parsed


def _source_binding(value: Any, where: str) -> tuple[str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"ref", "fingerprint"}, where)
    return (
        _string(item.get("ref"), f"{where}.ref"),
        _string(item.get("fingerprint"), f"{where}.fingerprint"),
    )


def _target_binding(value: Any, where: str) -> tuple[str, str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"kind", "identifier", "identity_fingerprint"}, where)
    return (
        _token(item.get("kind"), f"{where}.kind"),
        _string(item.get("identifier"), f"{where}.identifier"),
        _string(item.get("identity_fingerprint"), f"{where}.identity_fingerprint"),
    )


def _observer(value: Any, where: str) -> tuple[str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"type", "identifier"}, where)
    observer_type = _string(item.get("type"), f"{where}.type", max_len=32)
    if observer_type not in {"human", "adapter", "workflow"}:
        raise ObservationGateError(
            f"{where}.type must be human, adapter, or workflow"
        )
    return observer_type, _string(
        item.get("identifier"), f"{where}.identifier", max_len=128
    )


def _evidence_bindings(value: Any, where: str) -> dict[str, tuple[str, str]]:
    if not isinstance(value, list):
        raise ObservationGateError(f"{where} must be a list")
    if len(value) > 32:
        raise ObservationGateError(f"{where} must contain at most 32 bindings")

    out: dict[str, tuple[str, str]] = {}
    for i, raw in enumerate(value):
        item_where = f"{where}[{i}]"
        item = _mapping(raw, item_where)
        _exact_keys(item, {"ref", "state", "fingerprint"}, item_where)
        ref = _string(item.get("ref"), f"{item_where}.ref")
        state = _string(item.get("state"), f"{item_where}.state", max_len=32)
        if state not in EVIDENCE_STATES:
            raise ObservationGateError(f"{item_where}.state is not an allowed evidence state")
        fingerprint = _string(
            item.get("fingerprint"), f"{item_where}.fingerprint"
        )
        if ref in out:
            raise ObservationGateError(f"{where} contains duplicate evidence ref {ref!r}")
        out[ref] = (state, fingerprint)
    return out


def _validate_observation(value: dict[str, Any], where: str) -> dict[str, Any]:
    _exact_keys(value, OBSERVATION_KEYS, where)
    if value.get("schema_version") != "0.1":
        raise ObservationGateError(f"{where}.schema_version must be '0.1'")
    if value.get("classification") != "BOUNDARY_OBSERVATION":
        raise ObservationGateError(
            f"{where}.classification must be BOUNDARY_OBSERVATION"
        )
    _string(value.get("observation_id"), f"{where}.observation_id", max_len=128)
    _string(value.get("task_id"), f"{where}.task_id", max_len=128)
    _string(value.get("handoff_fingerprint"), f"{where}.handoff_fingerprint")
    _target_binding(value.get("target_binding"), f"{where}.target_binding")
    _source_binding(value.get("authority_binding"), f"{where}.authority_binding")
    _source_binding(value.get("policy_binding"), f"{where}.policy_binding")
    _evidence_bindings(value.get("evidence_bindings"), f"{where}.evidence_bindings")
    _observer(value.get("observed_by"), f"{where}.observed_by")
    _timestamp(value.get("observed_at"), f"{where}.observed_at")
    return value


def evaluate_reky_gate(
    before: dict[str, Any],
    after: dict[str, Any],
) -> ReKYDecision:
    before = _validate_observation(_mapping(before, "before"), "before")
    after = _validate_observation(_mapping(after, "after"), "after")

    before_time = _timestamp(before["observed_at"], "before.observed_at")
    after_time = _timestamp(after["observed_at"], "after.observed_at")
    if after_time < before_time:
        raise ObservationGateError("after observation must not predate before observation")

    if before["task_id"] != after["task_id"]:
        raise ObservationGateError("before/after task_id mismatch")
    if before["handoff_fingerprint"] != after["handoff_fingerprint"]:
        raise ObservationGateError("before/after handoff_fingerprint mismatch")

    reasons: list[ReKYReason] = []

    def add(code: str, detail: str) -> None:
        reasons.append(ReKYReason(code=code, detail=detail))

    if _target_binding(before["target_binding"], "before.target_binding") != _target_binding(
        after["target_binding"], "after.target_binding"
    ):
        add("TARGET_BINDING_CHANGED", "target identity binding changed")

    if _source_binding(before["authority_binding"], "before.authority_binding") != _source_binding(
        after["authority_binding"], "after.authority_binding"
    ):
        add("AUTHORITY_BINDING_CHANGED", "authority reference or fingerprint changed")

    if _source_binding(before["policy_binding"], "before.policy_binding") != _source_binding(
        after["policy_binding"], "after.policy_binding"
    ):
        add("POLICY_BINDING_CHANGED", "policy reference or fingerprint changed")

    if _observer(before["observed_by"], "before.observed_by") != _observer(
        after["observed_by"], "after.observed_by"
    ):
        add("OBSERVER_CHANGED", "boundary observation source changed")

    before_evidence = _evidence_bindings(
        before["evidence_bindings"], "before.evidence_bindings"
    )
    after_evidence = _evidence_bindings(
        after["evidence_bindings"], "after.evidence_bindings"
    )

    before_refs = set(before_evidence)
    after_refs = set(after_evidence)
    if before_refs != after_refs:
        added = sorted(after_refs - before_refs)
        removed = sorted(before_refs - after_refs)
        detail = f"evidence binding set changed; added={added!r}, removed={removed!r}"
        add("EVIDENCE_SET_CHANGED", detail)

    for ref in sorted(before_refs & after_refs):
        before_state, before_fp = before_evidence[ref]
        after_state, after_fp = after_evidence[ref]
        if before_fp != after_fp:
            add(
                "EVIDENCE_FINGERPRINT_CHANGED",
                f"evidence {ref!r} fingerprint changed",
            )
        if before_state != after_state:
            add(
                "EVIDENCE_STATE_CHANGED",
                f"evidence {ref!r} state changed from {before_state} to {after_state}",
            )
        if after_state in DEGRADED_EVIDENCE_STATES:
            add(
                "EVIDENCE_DEGRADED",
                f"evidence {ref!r} is {after_state}",
            )

    outcome = "RE_KY" if reasons else "CONTINUE"

    return ReKYDecision(
        schema_version="0.1",
        task_id=before["task_id"],
        handoff_fingerprint=before["handoff_fingerprint"],
        before_observation_id=before["observation_id"],
        after_observation_id=after["observation_id"],
        before_fingerprint=stable_hash(before),
        after_fingerprint=stable_hash(after),
        outcome=outcome,
        reasons=[asdict(r) for r in reasons],
        authority_granted=False,
    )
