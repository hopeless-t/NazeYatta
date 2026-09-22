from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .evaluator import stable_hash


EVIDENCE_STATES = {"VERIFIED", "PRESENT", "STALE", "INVALID", "MISSING", "UNKNOWN"}

RECORD_KEYS = {
    "schema_version",
    "derivation_id",
    "classification",
    "task_id",
    "baseline_id",
    "baseline_fingerprint",
    "source_snapshots",
    "prepared_by",
    "derivation_method",
    "prepared_at",
    "semantic_correctness_claimed",
    "authority_granted",
}


class BaselineDerivationError(ValueError):
    """A baseline derivation record cannot be validated safely."""


@dataclass(frozen=True)
class BaselineDerivationFinding:
    code: str
    detail: str


@dataclass(frozen=True)
class BaselineDerivationResult:
    schema_version: str
    task_id: str
    baseline_id: str
    derivation_id: str
    baseline_fingerprint: str
    record_fingerprint: str
    outcome: str
    findings: list[dict[str, str]]
    semantic_correctness_verified: bool
    authority_granted: bool


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BaselineDerivationError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise BaselineDerivationError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise BaselineDerivationError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise BaselineDerivationError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise BaselineDerivationError(f"{where} must be at most {max_len} characters")
    return value


def _timestamp(value: Any, where: str) -> str:
    raw = _string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise BaselineDerivationError(f"{where} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise BaselineDerivationError(f"{where} must include a timezone")
    return raw


def _source_binding(value: Any, where: str) -> tuple[str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"ref", "observation_state", "binding_token"}, where)
    if item.get("observation_state") != "OBSERVED":
        raise BaselineDerivationError(f"{where}.observation_state must be OBSERVED")
    return (
        _string(item.get("ref"), f"{where}.ref"),
        _string(item.get("binding_token"), f"{where}.binding_token"),
    )


def _evidence_bindings(value: Any, where: str) -> dict[str, tuple[str, str]]:
    if not isinstance(value, list):
        raise BaselineDerivationError(f"{where} must be a list")
    if len(value) > 32:
        raise BaselineDerivationError(f"{where} must contain at most 32 bindings")

    out: dict[str, tuple[str, str]] = {}
    for i, raw in enumerate(value):
        item_where = f"{where}[{i}]"
        item = _mapping(raw, item_where)
        _exact_keys(
            item,
            {"ref", "observation_state", "state", "binding_token"},
            item_where,
        )
        if item.get("observation_state") != "OBSERVED":
            raise BaselineDerivationError(
                f"{item_where}.observation_state must be OBSERVED"
            )
        ref = _string(item.get("ref"), f"{item_where}.ref")
        state = _string(item.get("state"), f"{item_where}.state", max_len=32)
        if state not in EVIDENCE_STATES:
            raise BaselineDerivationError(
                f"{item_where}.state is not an allowed evidence state"
            )
        token = _string(item.get("binding_token"), f"{item_where}.binding_token")
        if ref in out:
            raise BaselineDerivationError(f"{where} contains duplicate evidence ref {ref!r}")
        out[ref] = (state, token)
    return out


def _source_snapshot_map(value: Any, where: str) -> dict[str, Any]:
    snapshots = _mapping(value, where)
    _exact_keys(
        snapshots,
        {"authority_binding", "policy_binding", "evidence_bindings"},
        where,
    )
    authority = _source_binding(
        snapshots.get("authority_binding"), f"{where}.authority_binding"
    )
    policy = _source_binding(
        snapshots.get("policy_binding"), f"{where}.policy_binding"
    )
    evidence = _evidence_bindings(
        snapshots.get("evidence_bindings"), f"{where}.evidence_bindings"
    )
    return {
        "authority": authority,
        "policy": policy,
        "evidence": evidence,
    }


def _validate_record(record: dict[str, Any]) -> None:
    _exact_keys(record, RECORD_KEYS, "record")
    if record.get("schema_version") != "0.1":
        raise BaselineDerivationError("record.schema_version must be '0.1'")
    if record.get("classification") != "BASELINE_DERIVATION_RECORD":
        raise BaselineDerivationError(
            "record.classification must be BASELINE_DERIVATION_RECORD"
        )
    _string(record.get("derivation_id"), "record.derivation_id", max_len=128)
    _string(record.get("task_id"), "record.task_id", max_len=128)
    _string(record.get("baseline_id"), "record.baseline_id", max_len=128)
    _string(record.get("baseline_fingerprint"), "record.baseline_fingerprint")
    _source_snapshot_map(record.get("source_snapshots"), "record.source_snapshots")

    prepared_by = _mapping(record.get("prepared_by"), "record.prepared_by")
    _exact_keys(prepared_by, {"type", "identifier"}, "record.prepared_by")
    if prepared_by.get("type") not in {"human", "adapter", "workflow"}:
        raise BaselineDerivationError(
            "record.prepared_by.type must be human, adapter, or workflow"
        )
    _string(prepared_by.get("identifier"), "record.prepared_by.identifier", max_len=128)

    method = _mapping(record.get("derivation_method"), "record.derivation_method")
    _exact_keys(method, {"type", "identifier", "version"}, "record.derivation_method")
    if method.get("type") not in {"manual", "deterministic_adapter", "workflow"}:
        raise BaselineDerivationError(
            "record.derivation_method.type must be manual, deterministic_adapter, or workflow"
        )
    _string(method.get("identifier"), "record.derivation_method.identifier", max_len=128)
    _string(method.get("version"), "record.derivation_method.version", max_len=128)

    _timestamp(record.get("prepared_at"), "record.prepared_at")

    if record.get("semantic_correctness_claimed") is not False:
        raise BaselineDerivationError(
            "record.semantic_correctness_claimed must be false"
        )
    if record.get("authority_granted") is not False:
        raise BaselineDerivationError("record.authority_granted must be false")


def _baseline_source_refs(baseline: dict[str, Any]) -> tuple[str, str, set[str]]:
    baseline = _mapping(baseline, "baseline")
    task_id = _string(baseline.get("task_id"), "baseline.task_id", max_len=128)
    baseline_id = _string(baseline.get("baseline_id"), "baseline.baseline_id", max_len=128)
    refs = _mapping(baseline.get("source_refs"), "baseline.source_refs")
    _exact_keys(refs, {"authority_ref", "policy_ref", "evidence_refs"}, "baseline.source_refs")
    authority_ref = _string(refs.get("authority_ref"), "baseline.source_refs.authority_ref")
    policy_ref = _string(refs.get("policy_ref"), "baseline.source_refs.policy_ref")
    evidence_refs_raw = refs.get("evidence_refs")
    if not isinstance(evidence_refs_raw, list):
        raise BaselineDerivationError("baseline.source_refs.evidence_refs must be a list")
    evidence_refs = {
        _string(v, f"baseline.source_refs.evidence_refs[{i}]")
        for i, v in enumerate(evidence_refs_raw)
    }
    if len(evidence_refs) != len(evidence_refs_raw):
        raise BaselineDerivationError("baseline.source_refs.evidence_refs contains duplicates")
    return task_id, baseline_id, authority_ref, policy_ref, evidence_refs


def validate_baseline_derivation(
    baseline: dict[str, Any],
    record: dict[str, Any],
    *,
    current_source_snapshots: dict[str, Any] | None = None,
) -> BaselineDerivationResult:
    _validate_record(_mapping(record, "record"))

    task_id, baseline_id, authority_ref, policy_ref, evidence_refs = _baseline_source_refs(
        baseline
    )
    baseline_fp = stable_hash(baseline)

    if record["task_id"] != task_id:
        raise BaselineDerivationError("record.task_id does not match baseline")
    if record["baseline_id"] != baseline_id:
        raise BaselineDerivationError("record.baseline_id does not match baseline")
    if record["baseline_fingerprint"] != baseline_fp:
        raise BaselineDerivationError(
            "record.baseline_fingerprint does not match baseline"
        )

    recorded = _source_snapshot_map(
        record["source_snapshots"], "record.source_snapshots"
    )
    if recorded["authority"][0] != authority_ref:
        raise BaselineDerivationError(
            "record authority ref does not match baseline source ref"
        )
    if recorded["policy"][0] != policy_ref:
        raise BaselineDerivationError(
            "record policy ref does not match baseline source ref"
        )
    if set(recorded["evidence"]) != evidence_refs:
        raise BaselineDerivationError(
            "record evidence refs do not exactly match baseline source refs"
        )

    findings: list[BaselineDerivationFinding] = []

    if current_source_snapshots is not None:
        current = _source_snapshot_map(
            current_source_snapshots, "current_source_snapshots"
        )
        if current["authority"][0] != authority_ref:
            raise BaselineDerivationError(
                "current authority ref does not match baseline source ref"
            )
        if current["policy"][0] != policy_ref:
            raise BaselineDerivationError(
                "current policy ref does not match baseline source ref"
            )
        if set(current["evidence"]) != evidence_refs:
            raise BaselineDerivationError(
                "current evidence refs do not exactly match baseline source refs"
            )

        if current["authority"][1] != recorded["authority"][1]:
            findings.append(
                BaselineDerivationFinding(
                    code="AUTHORITY_SOURCE_CHANGED",
                    detail="authority source binding token changed since derivation record",
                )
            )
        if current["policy"][1] != recorded["policy"][1]:
            findings.append(
                BaselineDerivationFinding(
                    code="POLICY_SOURCE_CHANGED",
                    detail="policy source binding token changed since derivation record",
                )
            )

        for ref in sorted(evidence_refs):
            recorded_state, recorded_token = recorded["evidence"][ref]
            current_state, current_token = current["evidence"][ref]
            if current_token != recorded_token:
                findings.append(
                    BaselineDerivationFinding(
                        code="EVIDENCE_SOURCE_CHANGED",
                        detail=f"evidence source {ref!r} binding token changed since derivation record",
                    )
                )
            if current_state != recorded_state:
                findings.append(
                    BaselineDerivationFinding(
                        code="EVIDENCE_STATE_CHANGED",
                        detail=f"evidence source {ref!r} state changed from {recorded_state} to {current_state}",
                    )
                )

    outcome = "SOURCE_CHANGED" if findings else "PROVENANCE_BOUND"

    return BaselineDerivationResult(
        schema_version="0.1",
        task_id=task_id,
        baseline_id=baseline_id,
        derivation_id=record["derivation_id"],
        baseline_fingerprint=baseline_fp,
        record_fingerprint=stable_hash(record),
        outcome=outcome,
        findings=[asdict(f) for f in findings],
        semantic_correctness_verified=False,
        authority_granted=False,
    )
