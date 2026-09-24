from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any

from .evaluator import stable_hash
from .fresh_handoff import FreshHandoff


TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,127}$")
EVIDENCE_STATES = {"VERIFIED", "PRESENT", "STALE", "INVALID", "MISSING", "UNKNOWN"}
DEGRADED_EVIDENCE_STATES = {"STALE", "INVALID", "MISSING", "UNKNOWN"}
OBSERVATION_STATES = {"OBSERVED", "CARRIED_FORWARD", "UNKNOWN"}

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


def _observation_state(value: Any, where: str) -> str:
    state = _string(value, where, max_len=32)
    if state not in OBSERVATION_STATES:
        raise ObservationGateError(f"{where} is not an allowed observation state")
    return state


def _binding_token(value: Any, observation_state: str, where: str) -> str | None:
    if observation_state == "OBSERVED":
        return _string(value, where)
    if value is not None:
        raise ObservationGateError(
            f"{where} must be null when observation_state is {observation_state}"
        )
    return None


def _source_binding(value: Any, where: str) -> tuple[str, str, str | None]:
    item = _mapping(value, where)
    _exact_keys(item, {"ref", "observation_state", "binding_token"}, where)
    ref = _string(item.get("ref"), f"{where}.ref")
    observation_state = _observation_state(
        item.get("observation_state"), f"{where}.observation_state"
    )
    token = _binding_token(
        item.get("binding_token"), observation_state, f"{where}.binding_token"
    )
    return ref, observation_state, token


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


def _evidence_bindings(
    value: Any, where: str
) -> dict[str, tuple[str, str, str | None]]:
    if not isinstance(value, list):
        raise ObservationGateError(f"{where} must be a list")
    if len(value) > 32:
        raise ObservationGateError(f"{where} must contain at most 32 bindings")

    out: dict[str, tuple[str, str, str | None]] = {}
    for i, raw in enumerate(value):
        item_where = f"{where}[{i}]"
        item = _mapping(raw, item_where)
        _exact_keys(
            item,
            {"ref", "observation_state", "state", "binding_token"},
            item_where,
        )
        ref = _string(item.get("ref"), f"{item_where}.ref")
        observation_state = _observation_state(
            item.get("observation_state"),
            f"{item_where}.observation_state",
        )
        state = _string(item.get("state"), f"{item_where}.state", max_len=32)
        if state not in EVIDENCE_STATES:
            raise ObservationGateError(
                f"{item_where}.state is not an allowed evidence state"
            )
        token = _binding_token(
            item.get("binding_token"),
            observation_state,
            f"{item_where}.binding_token",
        )
        if observation_state != "OBSERVED" and state != "UNKNOWN":
            raise ObservationGateError(
                f"{item_where}.state must be UNKNOWN when source is not OBSERVED"
            )
        if ref in out:
            raise ObservationGateError(
                f"{where} contains duplicate evidence ref {ref!r}"
            )
        out[ref] = (observation_state, state, token)
    return out


def _validate_observation(value: dict[str, Any], where: str) -> dict[str, Any]:
    _exact_keys(value, OBSERVATION_KEYS, where)
    if value.get("schema_version") != "0.2":
        raise ObservationGateError(f"{where}.schema_version must be '0.2'")
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


def _validated_handoff_fingerprint(handoff: FreshHandoff) -> str:
    if not isinstance(handoff, FreshHandoff):
        raise ObservationGateError("handoff must be a FreshHandoff")
    if handoff.classification != "KY_VALIDATED_HANDOFF":
        raise ObservationGateError(
            "handoff.classification must be KY_VALIDATED_HANDOFF"
        )
    if handoff.authority_granted is not False:
        raise ObservationGateError("handoff must not grant execution authority")
    if handoff.validity != {"mode": "single_bounce", "runtime_state_bound": False}:
        raise ObservationGateError("handoff validity contract is unsupported")
    return stable_hash(asdict(handoff))


def _assert_observation_binds_handoff(
    handoff: FreshHandoff,
    observation: dict[str, Any],
    *,
    where: str,
    expected_handoff_fingerprint: str,
) -> None:
    subject = f"{where} observation" if where else "observation"

    if observation["task_id"] != handoff.task_id:
        raise ObservationGateError(
            f"{subject} task_id does not bind to handoff"
        )
    if observation["handoff_fingerprint"] != expected_handoff_fingerprint:
        raise ObservationGateError(
            f"{subject} handoff_fingerprint does not bind to handoff"
        )

    target = _target_binding(
        observation["target_binding"], f"{where}.target_binding" if where else "target_binding"
    )
    if target[1] != handoff.intended_action["target"]:
        raise ObservationGateError(
            f"{subject} target does not bind to handoff intended target"
        )

    authority = _source_binding(
        observation["authority_binding"],
        f"{where}.authority_binding" if where else "authority_binding",
    )
    if authority[0] != handoff.source_refs["authority_ref"]:
        raise ObservationGateError(
            f"{subject} authority ref does not bind to handoff"
        )

    policy = _source_binding(
        observation["policy_binding"],
        f"{where}.policy_binding" if where else "policy_binding",
    )
    if policy[0] != handoff.source_refs["policy_ref"]:
        raise ObservationGateError(
            f"{subject} policy ref does not bind to handoff"
        )

    evidence = _evidence_bindings(
        observation["evidence_bindings"],
        f"{where}.evidence_bindings" if where else "evidence_bindings",
    )
    if set(evidence) != set(handoff.source_refs["evidence_refs"]):
        raise ObservationGateError(
            f"{subject} evidence refs do not bind to handoff"
        )


def validate_boundary_observation_for_handoff(
    handoff: FreshHandoff,
    observation: dict[str, Any],
) -> dict[str, Any]:
    """Validate one serialized Boundary Observation against one exact FreshHandoff.

    This is a read-only consumer-side validation step. It does not authenticate the
    observer/source, make the handoff runtime-state-bound, or grant authority.
    """
    handoff_fingerprint = _validated_handoff_fingerprint(handoff)
    checked = _validate_observation(
        _mapping(observation, "observation"),
        "observation",
    )
    _assert_observation_binds_handoff(
        handoff,
        checked,
        where="",
        expected_handoff_fingerprint=handoff_fingerprint,
    )
    return checked


def build_boundary_observation(
    handoff: FreshHandoff,
    *,
    observation_id: str,
    target_binding: dict[str, Any],
    source_snapshot: dict[str, Any],
    observed_by: dict[str, Any],
    observed_at: str,
) -> dict[str, Any]:
    """Build one handoff-bound Boundary Observation.

    This helper binds structure and references to the exact FreshHandoff. It does
    not authenticate the observer/source, grant authority, or make the handoff
    runtime-state-bound.
    """
    handoff_fingerprint = _validated_handoff_fingerprint(handoff)
    snapshot = _mapping(source_snapshot, "source_snapshot")
    _exact_keys(
        snapshot,
        {"authority_binding", "policy_binding", "evidence_bindings"},
        "source_snapshot",
    )

    observation = {
        "schema_version": "0.2",
        "observation_id": observation_id,
        "classification": "BOUNDARY_OBSERVATION",
        "task_id": handoff.task_id,
        "handoff_fingerprint": handoff_fingerprint,
        "target_binding": target_binding,
        "authority_binding": snapshot["authority_binding"],
        "policy_binding": snapshot["policy_binding"],
        "evidence_bindings": snapshot["evidence_bindings"],
        "observed_by": observed_by,
        "observed_at": observed_at,
    }

    return validate_boundary_observation_for_handoff(handoff, observation)


def evaluate_reky_gate(
    handoff: FreshHandoff,
    before: dict[str, Any],
    after: dict[str, Any],
) -> ReKYDecision:
    expected_handoff_fingerprint = _validated_handoff_fingerprint(handoff)

    before = _validate_observation(_mapping(before, "before"), "before")
    after = _validate_observation(_mapping(after, "after"), "after")

    before_time = _timestamp(before["observed_at"], "before.observed_at")
    after_time = _timestamp(after["observed_at"], "after.observed_at")
    if after_time < before_time:
        raise ObservationGateError(
            "after observation must not predate before observation"
        )

    _assert_observation_binds_handoff(
        handoff,
        before,
        where="before",
        expected_handoff_fingerprint=expected_handoff_fingerprint,
    )

    if before["task_id"] != after["task_id"]:
        raise ObservationGateError("before/after task_id mismatch")
    if before["handoff_fingerprint"] != after["handoff_fingerprint"]:
        raise ObservationGateError(
            "before/after handoff_fingerprint mismatch"
        )

    reasons: list[ReKYReason] = []

    def add(code: str, detail: str) -> None:
        reasons.append(ReKYReason(code=code, detail=detail))

    if _target_binding(
        before["target_binding"], "before.target_binding"
    ) != _target_binding(after["target_binding"], "after.target_binding"):
        add("TARGET_BINDING_CHANGED", "target identity binding changed")

    before_authority = _source_binding(
        before["authority_binding"], "before.authority_binding"
    )
    after_authority = _source_binding(
        after["authority_binding"], "after.authority_binding"
    )
    if before_authority[0] != after_authority[0]:
        add("AUTHORITY_BINDING_CHANGED", "authority reference changed")
    if before_authority[1] != "OBSERVED" or after_authority[1] != "OBSERVED":
        add(
            "AUTHORITY_NOT_OBSERVED",
            "authority binding was not observed in both boundary snapshots",
        )
    elif before_authority[2] != after_authority[2]:
        add("AUTHORITY_BINDING_CHANGED", "authority binding token changed")

    before_policy = _source_binding(
        before["policy_binding"], "before.policy_binding"
    )
    after_policy = _source_binding(
        after["policy_binding"], "after.policy_binding"
    )
    if before_policy[0] != after_policy[0]:
        add("POLICY_BINDING_CHANGED", "policy reference changed")
    if before_policy[1] != "OBSERVED" or after_policy[1] != "OBSERVED":
        add(
            "POLICY_NOT_OBSERVED",
            "policy binding was not observed in both boundary snapshots",
        )
    elif before_policy[2] != after_policy[2]:
        add("POLICY_BINDING_CHANGED", "policy binding token changed")

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
        add(
            "EVIDENCE_SET_CHANGED",
            f"evidence binding set changed; added={added!r}, removed={removed!r}",
        )

    for ref in sorted(before_refs & after_refs):
        before_obs, before_state, before_token = before_evidence[ref]
        after_obs, after_state, after_token = after_evidence[ref]

        if before_obs != "OBSERVED" or after_obs != "OBSERVED":
            add(
                "EVIDENCE_NOT_OBSERVED",
                f"evidence {ref!r} was not observed in both boundary snapshots",
            )
            continue

        if before_token != after_token:
            add(
                "EVIDENCE_BINDING_TOKEN_CHANGED",
                f"evidence {ref!r} binding token changed",
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
