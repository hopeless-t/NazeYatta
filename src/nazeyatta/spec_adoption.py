from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .evaluator import stable_hash


SPEC_KEYS = {
    "schema_version",
    "spec_id",
    "classification",
    "version",
    "source_classifications",
    "mapping",
    "semantic_correctness_claimed",
    "authority_granted",
}

RECORD_KEYS = {
    "schema_version",
    "adoption_id",
    "classification",
    "spec_id",
    "spec_version",
    "spec_fingerprint",
    "authority_ref",
    "scope",
    "status",
    "valid_from",
    "expires_at",
    "recorded_by",
    "recorded_at",
    "authority_authenticated",
    "normative_correctness_verified",
    "authority_granted",
}

SCOPE_KEYS = {
    "task_id",
    "authority_source_ref",
    "policy_source_ref",
    "evidence_source_refs",
}


class SpecAdoptionError(ValueError):
    """A spec adoption record cannot be evaluated safely."""


@dataclass(frozen=True)
class SpecAdoptionFinding:
    code: str
    detail: str


@dataclass(frozen=True)
class SpecAdoptionResult:
    schema_version: str
    adoption_id: str
    spec_id: str
    spec_version: str
    spec_fingerprint: str
    record_fingerprint: str
    scope_fingerprint: str
    evaluated_at: str
    outcome: str
    findings: list[dict[str, str]]
    authority_authenticated: bool
    normative_correctness_verified: bool
    authority_granted: bool


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpecAdoptionError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise SpecAdoptionError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise SpecAdoptionError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise SpecAdoptionError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise SpecAdoptionError(f"{where} must be at most {max_len} characters")
    return value


def _timestamp(value: Any, where: str) -> datetime:
    raw = _string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SpecAdoptionError(f"{where} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise SpecAdoptionError(f"{where} must include a timezone")
    return parsed


def _scope(value: Any, where: str) -> dict[str, Any]:
    scope = _mapping(value, where)
    _exact_keys(scope, SCOPE_KEYS, where)
    _string(scope.get("task_id"), f"{where}.task_id", max_len=128)
    _string(scope.get("authority_source_ref"), f"{where}.authority_source_ref")
    _string(scope.get("policy_source_ref"), f"{where}.policy_source_ref")
    refs = scope.get("evidence_source_refs")
    if not isinstance(refs, list):
        raise SpecAdoptionError(f"{where}.evidence_source_refs must be a list")
    if len(refs) > 32:
        raise SpecAdoptionError(
            f"{where}.evidence_source_refs must contain at most 32 refs"
        )
    checked = [_string(v, f"{where}.evidence_source_refs[{i}]") for i, v in enumerate(refs)]
    if len(checked) != len(set(checked)):
        raise SpecAdoptionError(f"{where}.evidence_source_refs contains duplicates")
    return {
        "task_id": scope["task_id"],
        "authority_source_ref": scope["authority_source_ref"],
        "policy_source_ref": scope["policy_source_ref"],
        "evidence_source_refs": list(scope["evidence_source_refs"]),
    }


def _validate_spec(spec: dict[str, Any]) -> None:
    _exact_keys(spec, SPEC_KEYS, "spec")
    if spec.get("schema_version") != "0.1":
        raise SpecAdoptionError("spec.schema_version must be '0.1'")
    if spec.get("classification") != "DOGFOOD_BASELINE_DERIVATION_SPEC":
        raise SpecAdoptionError(
            "spec.classification must be DOGFOOD_BASELINE_DERIVATION_SPEC"
        )
    _string(spec.get("spec_id"), "spec.spec_id", max_len=128)
    _string(spec.get("version"), "spec.version", max_len=128)
    if spec.get("semantic_correctness_claimed") is not False:
        raise SpecAdoptionError("spec.semantic_correctness_claimed must be false")
    if spec.get("authority_granted") is not False:
        raise SpecAdoptionError("spec.authority_granted must be false")


def _validate_record(record: dict[str, Any]) -> None:
    _exact_keys(record, RECORD_KEYS, "record")
    if record.get("schema_version") != "0.1":
        raise SpecAdoptionError("record.schema_version must be '0.1'")
    if record.get("classification") != "SPEC_ADOPTION_RECORD":
        raise SpecAdoptionError("record.classification must be SPEC_ADOPTION_RECORD")

    _string(record.get("adoption_id"), "record.adoption_id", max_len=128)
    _string(record.get("spec_id"), "record.spec_id", max_len=128)
    _string(record.get("spec_version"), "record.spec_version", max_len=128)
    _string(record.get("spec_fingerprint"), "record.spec_fingerprint")
    _string(record.get("authority_ref"), "record.authority_ref")
    _scope(record.get("scope"), "record.scope")

    if record.get("status") not in {"ACTIVE", "REVOKED"}:
        raise SpecAdoptionError("record.status must be ACTIVE or REVOKED")

    valid_from = _timestamp(record.get("valid_from"), "record.valid_from")
    expires_raw = record.get("expires_at")
    if expires_raw is not None:
        expires_at = _timestamp(expires_raw, "record.expires_at")
        if expires_at <= valid_from:
            raise SpecAdoptionError("record.expires_at must be later than valid_from")

    recorded_by = _mapping(record.get("recorded_by"), "record.recorded_by")
    _exact_keys(recorded_by, {"type", "identifier"}, "record.recorded_by")
    if recorded_by.get("type") not in {"human", "workflow", "adapter"}:
        raise SpecAdoptionError(
            "record.recorded_by.type must be human, workflow, or adapter"
        )
    _string(recorded_by.get("identifier"), "record.recorded_by.identifier", max_len=128)
    recorded_at = _timestamp(record.get("recorded_at"), "record.recorded_at")
    if valid_from < recorded_at:
        raise SpecAdoptionError(
            "record.valid_from must not predate record.recorded_at"
        )

    if record.get("authority_authenticated") is not False:
        raise SpecAdoptionError("record.authority_authenticated must be false")
    if record.get("normative_correctness_verified") is not False:
        raise SpecAdoptionError(
            "record.normative_correctness_verified must be false"
        )
    if record.get("authority_granted") is not False:
        raise SpecAdoptionError("record.authority_granted must be false")


def evaluate_spec_adoption(
    spec: dict[str, Any],
    record: dict[str, Any],
    *,
    expected_scope: dict[str, Any],
    evaluated_at: str,
) -> SpecAdoptionResult:
    spec = _mapping(spec, "spec")
    record = _mapping(record, "record")
    _validate_spec(spec)
    _validate_record(record)

    current_scope = _scope(expected_scope, "expected_scope")
    evaluated_dt = _timestamp(evaluated_at, "evaluated_at")

    spec_fp = stable_hash(spec)
    findings: list[SpecAdoptionFinding] = []

    def add(code: str, detail: str) -> None:
        findings.append(SpecAdoptionFinding(code=code, detail=detail))

    if record["spec_id"] != spec["spec_id"]:
        add("SPEC_ID_MISMATCH", "record spec_id does not match supplied spec")
    if record["spec_version"] != spec["version"]:
        add("SPEC_VERSION_MISMATCH", "record spec_version does not match supplied spec")
    if record["spec_fingerprint"] != spec_fp:
        add(
            "SPEC_FINGERPRINT_MISMATCH",
            "record spec_fingerprint does not match supplied spec",
        )

    record_scope = _scope(record["scope"], "record.scope")
    if record_scope != current_scope:
        add("SCOPE_MISMATCH", "record scope does not match expected scope")

    if record["status"] != "ACTIVE":
        add("STATUS_NOT_ACTIVE", f"record status is {record['status']}")

    valid_from = _timestamp(record["valid_from"], "record.valid_from")
    if evaluated_dt < valid_from:
        add("NOT_YET_VALID", "evaluated_at predates record.valid_from")

    if record["expires_at"] is not None:
        expires_at = _timestamp(record["expires_at"], "record.expires_at")
        if evaluated_dt >= expires_at:
            add("EXPIRED", "evaluated_at is at or after record.expires_at")

    outcome = "RECORD_NOT_ADMISSIBLE" if findings else "RECORD_BOUND"

    return SpecAdoptionResult(
        schema_version="0.1",
        adoption_id=record["adoption_id"],
        spec_id=spec["spec_id"],
        spec_version=spec["version"],
        spec_fingerprint=spec_fp,
        record_fingerprint=stable_hash(record),
        scope_fingerprint=stable_hash(current_scope),
        evaluated_at=evaluated_at,
        outcome=outcome,
        findings=[asdict(f) for f in findings],
        authority_authenticated=False,
        normative_correctness_verified=False,
        authority_granted=False,
    )
