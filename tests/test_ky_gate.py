from dataclasses import asdict
from pathlib import Path

import pytest

from nazeyatta.evaluator import load_yaml
from nazeyatta.ky_gate import KYGateError, evaluate_ky_gate

ROOT = Path(__file__).resolve().parents[1]


def load_examples():
    declaration = load_yaml(ROOT / "examples/worker-ky-preview.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-preview.yaml")
    return declaration, baseline


def test_matching_worker_ky_passes_without_granting_authority():
    declaration, baseline = load_examples()
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "PASS"
    assert result.findings == []
    assert result.authority_granted is False


def test_intended_production_action_blocks():
    declaration, baseline = load_examples()
    declaration["intended_action"]["target"] = "production"
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "BLOCK"
    codes = {f["code"] for f in result.findings}
    assert "INTENDED_ACTION_NOT_ALLOWED" in codes
    assert "INTENDED_ACTION_FORBIDDEN" in codes


def test_worker_claiming_extra_allowed_scope_blocks():
    declaration, baseline = load_examples()
    declaration["understood_allowed_scope"].append(
        {"operation": "deploy", "target": "production"}
    )
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "BLOCK"
    assert any(f["code"] == "WORKER_SCOPE_EXCEEDS_BASELINE" for f in result.findings)


def test_worker_missing_forbidden_scope_requires_review():
    declaration, baseline = load_examples()
    declaration["understood_forbidden_scope"] = [
        {"operation": "deploy", "target": "production"}
    ]
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "REVIEW"
    assert any(f["code"] == "FORBIDDEN_SCOPE_NOT_RECOGNIZED" for f in result.findings)


def test_worker_missing_required_hazard_requires_review():
    declaration, baseline = load_examples()
    declaration["recognized_hazards"] = [
        item for item in declaration["recognized_hazards"]
        if item["id"] != "secret_exposure"
    ]
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "REVIEW"
    assert any(f["code"] == "REQUIRED_HAZARD_NOT_RECOGNIZED" for f in result.findings)


def test_worker_missing_required_control_requires_review():
    declaration, baseline = load_examples()
    declaration["planned_controls"] = [
        item for item in declaration["planned_controls"]
        if item["id"] != "avoid_production_secrets"
    ]
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "REVIEW"
    assert any(f["code"] == "REQUIRED_CONTROL_NOT_DECLARED" for f in result.findings)


def test_worker_missing_required_stop_condition_requires_review():
    declaration, baseline = load_examples()
    declaration["stop_conditions"] = [
        item for item in declaration["stop_conditions"]
        if item["id"] != "authority_unknown"
    ]
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "REVIEW"
    assert any(f["code"] == "REQUIRED_STOP_CONDITION_NOT_DECLARED" for f in result.findings)


def test_task_mismatch_blocks():
    declaration, baseline = load_examples()
    baseline["task_id"] = "OTHER-TASK"
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "BLOCK"
    assert any(f["code"] == "TASK_ID_MISMATCH" for f in result.findings)


def test_worker_self_contradiction_blocks():
    declaration, baseline = load_examples()
    declaration["understood_forbidden_scope"].append(
        {"operation": "deploy", "target": "preview"}
    )
    result = evaluate_ky_gate(declaration, baseline)
    assert result.outcome == "BLOCK"
    assert any(f["code"] == "WORKER_SCOPE_SELF_CONTRADICTION" for f in result.findings)


def test_fingerprints_are_deterministic():
    declaration, baseline = load_examples()
    a = evaluate_ky_gate(declaration, baseline)
    b = evaluate_ky_gate(declaration, baseline)
    assert a.declaration_fingerprint == b.declaration_fingerprint
    assert a.baseline_fingerprint == b.baseline_fingerprint
    assert asdict(a) == asdict(b)


def test_invalid_baseline_overlap_is_rejected():
    declaration, baseline = load_examples()
    baseline["forbidden_actions"].append(
        {"operation": "deploy", "target": "preview"}
    )
    with pytest.raises(KYGateError, match="must not overlap"):
        evaluate_ky_gate(declaration, baseline)


def test_wrong_classification_is_rejected():
    declaration, baseline = load_examples()
    declaration["classification"] = "EVIDENCE"
    with pytest.raises(KYGateError, match="WORKER_SELF_REPORT"):
        evaluate_ky_gate(declaration, baseline)


def test_wrong_schema_version_is_rejected():
    declaration, baseline = load_examples()
    declaration["schema_version"] = "0.1"
    with pytest.raises(KYGateError, match="schema_version"):
        evaluate_ky_gate(declaration, baseline)


def test_non_normalized_action_token_is_rejected():
    declaration, baseline = load_examples()
    declaration["intended_action"]["target"] = "Preview Environment"
    with pytest.raises(KYGateError, match="normalized lowercase token"):
        evaluate_ky_gate(declaration, baseline)


def test_extra_declaration_field_is_rejected():
    declaration, baseline = load_examples()
    declaration["reasoning"] = "hidden reasoning should not be accepted"
    with pytest.raises(KYGateError, match="unsupported keys"):
        evaluate_ky_gate(declaration, baseline)


def test_missing_baseline_source_refs_is_rejected():
    declaration, baseline = load_examples()
    del baseline["source_refs"]
    with pytest.raises(KYGateError, match="missing required keys"):
        evaluate_ky_gate(declaration, baseline)


def test_invalid_baseline_preparer_is_rejected():
    declaration, baseline = load_examples()
    baseline["prepared_by"]["type"] = "worker"
    with pytest.raises(KYGateError, match="human, adapter, or workflow"):
        evaluate_ky_gate(declaration, baseline)


def test_naive_declaration_timestamp_is_rejected():
    declaration, baseline = load_examples()
    declaration["declared_at"] = "2026-09-22T00:00:00"
    with pytest.raises(KYGateError, match="timezone"):
        evaluate_ky_gate(declaration, baseline)


def test_naive_baseline_timestamp_is_rejected():
    declaration, baseline = load_examples()
    baseline["prepared_at"] = "2026-09-22T00:00:00"
    with pytest.raises(KYGateError, match="timezone"):
        evaluate_ky_gate(declaration, baseline)
