from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from nazeyatta.evaluator import load_yaml, stable_hash
from nazeyatta.policy_provenance import (
    PolicyProvenanceError,
    evaluate_policy_provenance,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policies/generic/rules.yaml"

POLICY_REF = "policy://nazeyatta/generic-v0.1"
SOURCE_REF = "repo://policies/generic/rules.yaml"
SCOPE_REF = "scope://nazeyatta/research-default"
AUTHORITY_REF = "authority://nazeyatta/project-policy-maintainers"
RECORDED_SOURCE_TOKEN = "gitblob:4e142217c2517534f3c42090abfd75958701a701"


def _source_token() -> str:
    payload = POLICY_PATH.read_bytes()
    header = f"blob {len(payload)}\\0".encode("ascii")
    return "gitblob:" + hashlib.sha1(header + payload).hexdigest()


def _record(**overrides):
    policies = load_yaml(POLICY_PATH)
    record = {
        "schema_version": "0.1",
        "provenance_id": "POLICY-PROV-GENERIC-001",
        "classification": "POLICY_PROVENANCE_RECORD",
        "policy_bundle_id": policies["policy_bundle"]["id"],
        "policy_ref": POLICY_REF,
        "policy_bundle_fingerprint": stable_hash(policies),
        "source_ref": SOURCE_REF,
        "source_binding_token": RECORDED_SOURCE_TOKEN,
        "claimed_authority_ref": AUTHORITY_REF,
        "scope_ref": SCOPE_REF,
        "status": "ACTIVE",
        "valid_from": "2026-09-24T00:00:00+00:00",
        "expires_at": None,
        "recorded_by": {
            "type": "workflow",
            "identifier": "policy-provenance-test",
        },
        "recorded_at": "2026-09-24T00:00:00+00:00",
        "authority_authenticated": False,
        "normative_correctness_verified": False,
        "authority_granted": False,
    }
    record.update(overrides)
    return policies, record


def _evaluate(policies, record, **overrides):
    kwargs = {
        "expected_policy_ref": POLICY_REF,
        "expected_source_ref": SOURCE_REF,
        "expected_scope_ref": SCOPE_REF,
        "evaluated_at": "2026-09-24T00:01:00+00:00",
        "current_source_binding_token": _source_token(),
    }
    kwargs.update(overrides)
    return evaluate_policy_provenance(policies, record, **kwargs)


def test_actual_generic_policy_provenance_binds_without_authority_claim():
    policies, record = _record()
    result = _evaluate(policies, record)

    assert result.policy_bundle_id == "nazeyatta-generic-v0.1"
    assert result.policy_bundle_fingerprint == stable_hash(policies)
    assert _source_token() == RECORDED_SOURCE_TOKEN
    assert result.source_binding_token == RECORDED_SOURCE_TOKEN
    assert result.claimed_authority_ref == AUTHORITY_REF
    assert result.outcome == "PROVENANCE_BOUND"
    assert result.findings == []
    assert result.authority_authenticated is False
    assert result.normative_correctness_verified is False
    assert result.authority_granted is False


def test_policy_provenance_result_is_deterministic():
    policies, record = _record()
    a = _evaluate(policies, record)
    b = _evaluate(policies, record)

    assert asdict(a) == asdict(b)
    assert stable_hash(asdict(a)) == stable_hash(asdict(b))


def test_changed_source_binding_is_reported_without_reinterpreting_policy():
    policies, record = _record()
    result = _evaluate(
        policies,
        record,
        current_source_binding_token="sha256:" + "0" * 64,
    )

    assert result.outcome == "SOURCE_CHANGED"
    assert [f["code"] for f in result.findings] == ["SOURCE_BINDING_CHANGED"]
    assert result.authority_authenticated is False
    assert result.normative_correctness_verified is False


def test_forged_policy_fingerprint_is_not_admissible():
    policies, record = _record(
        policy_bundle_fingerprint="sha256:" + "f" * 64
    )
    result = _evaluate(policies, record)

    assert result.outcome == "PROVENANCE_NOT_ADMISSIBLE"
    assert any(
        f["code"] == "POLICY_FINGERPRINT_MISMATCH"
        for f in result.findings
    )


def test_revoked_policy_provenance_is_not_admissible():
    policies, record = _record(status="REVOKED")
    result = _evaluate(policies, record)

    assert result.outcome == "PROVENANCE_NOT_ADMISSIBLE"
    assert any(f["code"] == "STATUS_NOT_ACTIVE" for f in result.findings)


def test_expired_policy_provenance_is_not_admissible():
    policies, record = _record(
        expires_at="2026-09-24T00:00:30+00:00"
    )
    result = _evaluate(policies, record)

    assert result.outcome == "PROVENANCE_NOT_ADMISSIBLE"
    assert any(f["code"] == "EXPIRED" for f in result.findings)


def test_scope_mismatch_is_not_admissible():
    policies, record = _record()
    result = _evaluate(
        policies,
        record,
        expected_scope_ref="scope://other",
    )

    assert result.outcome == "PROVENANCE_NOT_ADMISSIBLE"
    assert any(f["code"] == "SCOPE_REF_MISMATCH" for f in result.findings)


def test_valid_from_cannot_predate_recorded_at():
    policies, record = _record(
        valid_from="2026-09-23T23:59:59+00:00"
    )

    with pytest.raises(
        PolicyProvenanceError,
        match="valid_from must not predate",
    ):
        _evaluate(policies, record)


def test_policy_provenance_schema_preserves_false_authority_claims():
    schema = json.loads(
        (
            ROOT / "schemas/policy-provenance-record.schema.json"
        ).read_text(encoding="utf-8")
    )
    props = schema["properties"]

    assert props["schema_version"]["const"] == "0.1"
    assert props["classification"]["const"] == "POLICY_PROVENANCE_RECORD"
    assert set(props["status"]["enum"]) == {"ACTIVE", "REVOKED"}
    assert props["authority_authenticated"]["const"] is False
    assert props["normative_correctness_verified"]["const"] is False
    assert props["authority_granted"]["const"] is False

    _, record = _record()
    assert set(schema["required"]) == set(record)
    assert set(props) == set(record)
