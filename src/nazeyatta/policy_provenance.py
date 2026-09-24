from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .evaluator import stable_hash


RECORD_KEYS = {
    "schema_version",
    "provenance_id",
    "classification",
    "policy_bundle_id",
    "policy_ref",
    "policy_bundle_fingerprint",
    "source_ref",
    "source_binding_token",
    "claimed_authority_ref",
    "scope_ref",
    "status",
    "valid_from",
    "expires_at",
    "recorded_by",
    "recorded_at",
    "authority_authenticated",
    "normative_correctness_verified",
    "authority_granted",
}


class PolicyProvenanceError(ValueError):
    """A policy provenance record cannot be evaluated safely."""


@dataclass(frozen=True)
class PolicyProvenanceFinding:
    code: str
    detail: str


@dataclass(frozen=True)
class PolicyProvenanceResult:
    schema_version: str
    provenance_id: str
    policy_bundle_id: str
    policy_ref: str
    policy_bundle_fingerprint: str
    record_fingerprint: str
    source_ref: str
    source_binding_token: str
    claimed_authority_ref: str
    scope_ref: str
    evaluated_at: str
    outcome: str
    findings: list[dict[str, str]]
    authority_authenticated: bool
    normative_correctness_verified: bool
    authority_granted: bool


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyProvenanceError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise PolicyProvenanceError(
            f"{where} is missing required keys: {sorted(missing)!r}"
        )
    if extra:
        raise PolicyProvenanceError(
            f"{where} has unsupported keys: {sorted(extra)!r}"
        )


def _string(value: Any, where: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value:
        raise PolicyProvenanceError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise PolicyProvenanceError(
            f"{where} must be at most {max_len} characters"
        )
    return value


def _timestamp(value: Any, where: str) -> datetime:
    raw = _string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise PolicyProvenanceError(
            f"{where} must be an ISO-8601 date-time"
        ) from exc
    if parsed.tzinfo is None:
        raise PolicyProvenanceError(f"{where} must include a timezone")
    return parsed


def _policy_bundle_id(policies: dict[str, Any]) -> str:
    root = _mapping(policies, "policies")
    bundle = _mapping(root.get("policy_bundle"), "policies.policy_bundle")
    return _string(
        bundle.get("id"),
        "policies.policy_bundle.id",
        max_len=128,
    )


def _validate_record(record: dict[str, Any]) -> None:
    _exact_keys(record, RECORD_KEYS, "record")
    if record.get("schema_version") != "0.1":
        raise PolicyProvenanceError("record.schema_version must be '0.1'")
    if record.get("classification") != "POLICY_PROVENANCE_RECORD":
        raise PolicyProvenanceError(
            "record.classification must be POLICY_PROVENANCE_RECORD"
        )

    for key in (
        "provenance_id",
        "policy_bundle_id",
        "policy_ref",
        "policy_bundle_fingerprint",
        "source_ref",
        "source_binding_token",
        "claimed_authority_ref",
        "scope_ref",
    ):
        _string(record.get(key), f"record.{key}")

    if record.get("status") not in {"ACTIVE", "REVOKED"}:
        raise PolicyProvenanceError("record.status must be ACTIVE or REVOKED")

    valid_from = _timestamp(record.get("valid_from"), "record.valid_from")
    recorded_at = _timestamp(record.get("recorded_at"), "record.recorded_at")
    if valid_from < recorded_at:
        raise PolicyProvenanceError(
            "record.valid_from must not predate record.recorded_at"
        )

    expires_raw = record.get("expires_at")
    if expires_raw is not None:
        expires_at = _timestamp(expires_raw, "record.expires_at")
        if expires_at <= valid_from:
            raise PolicyProvenanceError(
                "record.expires_at must be later than valid_from"
            )

    recorded_by = _mapping(record.get("recorded_by"), "record.recorded_by")
    _exact_keys(
        recorded_by,
        {"type", "identifier"},
        "record.recorded_by",
    )
    if recorded_by.get("type") not in {"human", "workflow", "adapter"}:
        raise PolicyProvenanceError(
            "record.recorded_by.type must be human, workflow, or adapter"
        )
    _string(
        recorded_by.get("identifier"),
        "record.recorded_by.identifier",
        max_len=128,
    )

    if record.get("authority_authenticated") is not False:
        raise PolicyProvenanceError(
            "record.authority_authenticated must be false"
        )
    if record.get("normative_correctness_verified") is not False:
        raise PolicyProvenanceError(
            "record.normative_correctness_verified must be false"
        )
    if record.get("authority_granted") is not False:
        raise PolicyProvenanceError(
            "record.authority_granted must be false"
        )


def evaluate_policy_provenance(
    policies: dict[str, Any],
    record: dict[str, Any],
    *,
    expected_policy_ref: str,
    expected_source_ref: str,
    expected_scope_ref: str,
    evaluated_at: str,
    current_source_binding_token: str | None = None,
) -> PolicyProvenanceResult:
    policies = _mapping(policies, "policies")
    record = _mapping(record, "record")
    _validate_record(record)

    policy_bundle_id = _policy_bundle_id(policies)
    policy_fingerprint = stable_hash(policies)

    expected_policy_ref = _string(expected_policy_ref, "expected_policy_ref")
    expected_source_ref = _string(expected_source_ref, "expected_source_ref")
    expected_scope_ref = _string(expected_scope_ref, "expected_scope_ref")
    evaluated_dt = _timestamp(evaluated_at, "evaluated_at")

    if current_source_binding_token is not None:
        current_source_binding_token = _string(
            current_source_binding_token,
            "current_source_binding_token",
        )

    findings: list[PolicyProvenanceFinding] = []

    def add(code: str, detail: str) -> None:
        findings.append(PolicyProvenanceFinding(code=code, detail=detail))

    if record["policy_bundle_id"] != policy_bundle_id:
        add(
            "POLICY_BUNDLE_ID_MISMATCH",
            "record policy_bundle_id does not match supplied policy bundle",
        )
    if record["policy_bundle_fingerprint"] != policy_fingerprint:
        add(
            "POLICY_FINGERPRINT_MISMATCH",
            "record policy_bundle_fingerprint does not match supplied policy bundle",
        )
    if record["policy_ref"] != expected_policy_ref:
        add(
            "POLICY_REF_MISMATCH",
            "record policy_ref does not match expected policy_ref",
        )
    if record["source_ref"] != expected_source_ref:
        add(
            "SOURCE_REF_MISMATCH",
            "record source_ref does not match expected source_ref",
        )
    if record["scope_ref"] != expected_scope_ref:
        add(
            "SCOPE_REF_MISMATCH",
            "record scope_ref does not match expected scope_ref",
        )
    if record["status"] != "ACTIVE":
        add("STATUS_NOT_ACTIVE", f"record status is {record['status']}")

    valid_from = _timestamp(record["valid_from"], "record.valid_from")
    if evaluated_dt < valid_from:
        add("NOT_YET_VALID", "evaluated_at predates record.valid_from")

    if record["expires_at"] is not None:
        expires_at = _timestamp(record["expires_at"], "record.expires_at")
        if evaluated_dt >= expires_at:
            add("EXPIRED", "evaluated_at is at or after record.expires_at")

    if (
        current_source_binding_token is not None
        and current_source_binding_token != record["source_binding_token"]
    ):
        add(
            "SOURCE_BINDING_CHANGED",
            "current source binding token differs from the recorded source snapshot",
        )

    codes = {finding.code for finding in findings}
    if not findings:
        outcome = "PROVENANCE_BOUND"
    elif codes == {"SOURCE_BINDING_CHANGED"}:
        outcome = "SOURCE_CHANGED"
    else:
        outcome = "PROVENANCE_NOT_ADMISSIBLE"

    return PolicyProvenanceResult(
        schema_version="0.1",
        provenance_id=record["provenance_id"],
        policy_bundle_id=policy_bundle_id,
        policy_ref=record["policy_ref"],
        policy_bundle_fingerprint=policy_fingerprint,
        record_fingerprint=stable_hash(record),
        source_ref=record["source_ref"],
        source_binding_token=record["source_binding_token"],
        claimed_authority_ref=record["claimed_authority_ref"],
        scope_ref=record["scope_ref"],
        evaluated_at=evaluated_at,
        outcome=outcome,
        findings=[asdict(finding) for finding in findings],
        authority_authenticated=False,
        normative_correctness_verified=False,
        authority_granted=False,
    )
