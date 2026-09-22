from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from nazeyatta.spec_adoption import evaluate_spec_adoption

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "examples" / "dogfood-baseline-derivation-spec.json"
RECORD_PATH = ROOT / "examples" / "dogfood-spec-adoption-record.json"

EXPECTED_SCOPE = {
    "task_id": "DOGFOOD-BASELINE-DERIVATION-001",
    "authority_source_ref": "authority://dogfood/ci-safe-read-only",
    "policy_source_ref": "policy://dogfood/runtime-safe-read-v0-1",
    "evidence_source_refs": ["evidence://dogfood/fixture-exists"],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_active_exact_record_is_bound_without_authentication_claim():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=EXPECTED_SCOPE,
        evaluated_at="2026-09-22T17:16:00+00:00",
    )

    assert result.outcome == "RECORD_BOUND"
    assert result.findings == []
    assert result.authority_authenticated is False
    assert result.normative_correctness_verified is False
    assert result.authority_granted is False


def test_changed_spec_is_not_admissible():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    spec["mapping"]["required_hazard_ids"] = ["wrong_target"]

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=EXPECTED_SCOPE,
        evaluated_at="2026-09-22T17:16:00+00:00",
    )

    assert result.outcome == "RECORD_NOT_ADMISSIBLE"
    assert any(f["code"] == "SPEC_FINGERPRINT_MISMATCH" for f in result.findings)


def test_scope_mismatch_is_not_admissible():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    other_scope = deepcopy(EXPECTED_SCOPE)
    other_scope["task_id"] = "OTHER-TASK"

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=other_scope,
        evaluated_at="2026-09-22T17:16:00+00:00",
    )

    assert result.outcome == "RECORD_NOT_ADMISSIBLE"
    assert any(f["code"] == "SCOPE_MISMATCH" for f in result.findings)


def test_revoked_record_is_not_admissible():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    record["status"] = "REVOKED"

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=EXPECTED_SCOPE,
        evaluated_at="2026-09-22T17:16:00+00:00",
    )

    assert result.outcome == "RECORD_NOT_ADMISSIBLE"
    assert any(f["code"] == "STATUS_NOT_ACTIVE" for f in result.findings)


def test_not_yet_valid_record_is_not_admissible():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=EXPECTED_SCOPE,
        evaluated_at="2026-09-22T17:14:59+00:00",
    )

    assert result.outcome == "RECORD_NOT_ADMISSIBLE"
    assert any(f["code"] == "NOT_YET_VALID" for f in result.findings)


def test_expired_record_is_not_admissible():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    record["expires_at"] = "2026-09-22T17:17:00+00:00"

    result = evaluate_spec_adoption(
        spec,
        record,
        expected_scope=EXPECTED_SCOPE,
        evaluated_at="2026-09-22T17:17:00+00:00",
    )

    assert result.outcome == "RECORD_NOT_ADMISSIBLE"
    assert any(f["code"] == "EXPIRED" for f in result.findings)


def test_record_cannot_claim_authenticated_authority():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    record["authority_authenticated"] = True

    import pytest
    with pytest.raises(Exception, match="authority_authenticated"):
        evaluate_spec_adoption(
            spec,
            record,
            expected_scope=EXPECTED_SCOPE,
            evaluated_at="2026-09-22T17:16:00+00:00",
        )


def test_record_cannot_claim_normative_correctness():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    record["normative_correctness_verified"] = True

    import pytest
    with pytest.raises(Exception, match="normative_correctness_verified"):
        evaluate_spec_adoption(
            spec,
            record,
            expected_scope=EXPECTED_SCOPE,
            evaluated_at="2026-09-22T17:16:00+00:00",
        )


def test_record_cannot_grant_execution_authority():
    spec = load_json(SPEC_PATH)
    record = load_json(RECORD_PATH)
    record["authority_granted"] = True

    import pytest
    with pytest.raises(Exception, match="authority_granted"):
        evaluate_spec_adoption(
            spec,
            record,
            expected_scope=EXPECTED_SCOPE,
            evaluated_at="2026-09-22T17:16:00+00:00",
        )
