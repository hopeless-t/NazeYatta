from dataclasses import asdict
from pathlib import Path

import pytest

from nazeyatta.evaluator import load_yaml, stable_hash
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.reky_gate import ObservationGateError, evaluate_reky_gate

ROOT = Path(__file__).resolve().parents[1]


def load_context():
    declaration = load_yaml(ROOT / "examples/worker-ky-preview.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-preview.yaml")
    gate = evaluate_ky_gate(declaration, baseline)
    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )

    before = load_yaml(ROOT / "examples/boundary-before.yaml")
    after = load_yaml(ROOT / "examples/boundary-after.yaml")
    handoff_fp = stable_hash(asdict(handoff))
    before["handoff_fingerprint"] = handoff_fp
    after["handoff_fingerprint"] = handoff_fp
    return handoff, before, after


def test_unchanged_boundary_continues_without_granting_authority():
    handoff, before, after = load_context()
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "CONTINUE"
    assert result.reasons == []
    assert result.authority_granted is False


def test_target_binding_change_requires_reky():
    handoff, before, after = load_context()
    after["target_binding"]["identifier"] = "production"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "TARGET_BINDING_CHANGED" for r in result.reasons)


def test_authority_binding_change_requires_reky():
    handoff, before, after = load_context()
    after["authority_binding"]["fingerprint"] = "sha256:authority-v2"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "AUTHORITY_BINDING_CHANGED" for r in result.reasons)


def test_policy_binding_change_requires_reky():
    handoff, before, after = load_context()
    after["policy_binding"]["fingerprint"] = "sha256:policy-v2"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "POLICY_BINDING_CHANGED" for r in result.reasons)


def test_observer_change_requires_reky():
    handoff, before, after = load_context()
    after["observed_by"]["identifier"] = "different-adapter"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "OBSERVER_CHANGED" for r in result.reasons)


def test_evidence_set_change_requires_reky():
    handoff, before, after = load_context()
    after["evidence_bindings"].append(
        {
            "ref": "evidence://extra",
            "state": "VERIFIED",
            "fingerprint": "sha256:extra",
        }
    )
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "EVIDENCE_SET_CHANGED" for r in result.reasons)


def test_evidence_fingerprint_change_requires_reky():
    handoff, before, after = load_context()
    after["evidence_bindings"][0]["fingerprint"] = "sha256:target-evidence-v2"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(r["code"] == "EVIDENCE_FINGERPRINT_CHANGED" for r in result.reasons)


def test_evidence_degradation_requires_reky():
    handoff, before, after = load_context()
    after["evidence_bindings"][0]["state"] = "STALE"
    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    codes = {r["code"] for r in result.reasons}
    assert "EVIDENCE_STATE_CHANGED" in codes
    assert "EVIDENCE_DEGRADED" in codes


def test_forged_matching_observation_handoff_fingerprint_is_rejected():
    handoff, before, after = load_context()
    before["handoff_fingerprint"] = "sha256:forged"
    after["handoff_fingerprint"] = "sha256:forged"
    with pytest.raises(ObservationGateError, match="does not bind to handoff"):
        evaluate_reky_gate(handoff, before, after)


def test_before_target_must_bind_to_handoff():
    handoff, before, after = load_context()
    before["target_binding"]["identifier"] = "production"
    after["target_binding"]["identifier"] = "production"
    with pytest.raises(ObservationGateError, match="target does not bind"):
        evaluate_reky_gate(handoff, before, after)


def test_before_authority_ref_must_bind_to_handoff():
    handoff, before, after = load_context()
    before["authority_binding"]["ref"] = "authority://other"
    after["authority_binding"]["ref"] = "authority://other"
    with pytest.raises(ObservationGateError, match="authority ref does not bind"):
        evaluate_reky_gate(handoff, before, after)


def test_before_policy_ref_must_bind_to_handoff():
    handoff, before, after = load_context()
    before["policy_binding"]["ref"] = "policy://other"
    after["policy_binding"]["ref"] = "policy://other"
    with pytest.raises(ObservationGateError, match="policy ref does not bind"):
        evaluate_reky_gate(handoff, before, after)


def test_before_evidence_refs_must_bind_to_handoff():
    handoff, before, after = load_context()
    before["evidence_bindings"] = []
    after["evidence_bindings"] = []
    with pytest.raises(ObservationGateError, match="evidence refs do not bind"):
        evaluate_reky_gate(handoff, before, after)


def test_unrelated_handoff_between_observations_cannot_be_compared():
    handoff, before, after = load_context()
    after["handoff_fingerprint"] = "sha256:other-handoff"
    with pytest.raises(ObservationGateError, match="handoff_fingerprint mismatch"):
        evaluate_reky_gate(handoff, before, after)


def test_unrelated_task_cannot_be_compared():
    handoff, before, after = load_context()
    after["task_id"] = "OTHER-TASK"
    with pytest.raises(ObservationGateError, match="task_id mismatch"):
        evaluate_reky_gate(handoff, before, after)


def test_after_observation_cannot_predate_before():
    handoff, before, after = load_context()
    after["observed_at"] = "2026-09-21T23:59:00+00:00"
    with pytest.raises(ObservationGateError, match="must not predate"):
        evaluate_reky_gate(handoff, before, after)


def test_decision_fingerprints_are_deterministic():
    handoff, before, after = load_context()
    a = evaluate_reky_gate(handoff, before, after)
    b = evaluate_reky_gate(handoff, before, after)
    assert asdict(a) == asdict(b)
