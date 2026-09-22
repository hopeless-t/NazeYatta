from dataclasses import asdict
from pathlib import Path

import pytest

from nazeyatta.evaluator import load_yaml
from nazeyatta.reky_gate import ObservationGateError, evaluate_reky_gate

ROOT = Path(__file__).resolve().parents[1]


def load_observations():
    before = load_yaml(ROOT / "examples/boundary-before.yaml")
    after = load_yaml(ROOT / "examples/boundary-after.yaml")
    return before, after


def test_unchanged_boundary_continues_without_granting_authority():
    before, after = load_observations()
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "CONTINUE"
    assert result.reasons == []
    assert result.authority_granted is False


def test_target_binding_change_requires_reky():
    before, after = load_observations()
    after["target_binding"]["identifier"] = "production"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "TARGET_BINDING_CHANGED" for r in result.reasons)


def test_authority_binding_change_requires_reky():
    before, after = load_observations()
    after["authority_binding"]["fingerprint"] = "sha256:authority-v2"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "AUTHORITY_BINDING_CHANGED" for r in result.reasons)


def test_policy_binding_change_requires_reky():
    before, after = load_observations()
    after["policy_binding"]["fingerprint"] = "sha256:policy-v2"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "POLICY_BINDING_CHANGED" for r in result.reasons)


def test_observer_change_requires_reky():
    before, after = load_observations()
    after["observed_by"]["identifier"] = "different-adapter"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "OBSERVER_CHANGED" for r in result.reasons)


def test_evidence_set_change_requires_reky():
    before, after = load_observations()
    after["evidence_bindings"].append(
        {
            "ref": "evidence://extra",
            "state": "VERIFIED",
            "fingerprint": "sha256:extra",
        }
    )
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "EVIDENCE_SET_CHANGED" for r in result.reasons)


def test_evidence_fingerprint_change_requires_reky():
    before, after = load_observations()
    after["evidence_bindings"][0]["fingerprint"] = "sha256:target-evidence-v2"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "EVIDENCE_FINGERPRINT_CHANGED" for r in result.reasons)


def test_evidence_degradation_requires_reky():
    before, after = load_observations()
    after["evidence_bindings"][0]["state"] = "STALE"
    result = evaluate_reky_gate(before, after)
    assert result.outcome == "RE_KY"
    codes = {r["code"] for r in result.reasons}
    assert "EVIDENCE_STATE_CHANGED" in codes
    assert "EVIDENCE_DEGRADED" in codes


def test_unrelated_handoff_cannot_be_compared():
    before, after = load_observations()
    after["handoff_fingerprint"] = "sha256:other-handoff"
    with pytest.raises(ObservationGateError, match="handoff_fingerprint mismatch"):
        evaluate_reky_gate(before, after)


def test_unrelated_task_cannot_be_compared():
    before, after = load_observations()
    after["task_id"] = "OTHER-TASK"
    with pytest.raises(ObservationGateError, match="task_id mismatch"):
        evaluate_reky_gate(before, after)


def test_after_observation_cannot_predate_before():
    before, after = load_observations()
    after["observed_at"] = "2026-09-21T23:59:00+00:00"
    with pytest.raises(ObservationGateError, match="must not predate"):
        evaluate_reky_gate(before, after)


def test_decision_fingerprints_are_deterministic():
    before, after = load_observations()
    a = evaluate_reky_gate(before, after)
    b = evaluate_reky_gate(before, after)
    assert asdict(a) == asdict(b)
