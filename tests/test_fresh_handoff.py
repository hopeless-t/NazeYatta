from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from nazeyatta.evaluator import load_yaml
from nazeyatta.fresh_handoff import FreshHandoffError, compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    declaration = load_yaml(ROOT / "examples/worker-ky-preview.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-preview.yaml")
    gate = evaluate_ky_gate(declaration, baseline)
    return declaration, baseline, gate


def test_pass_compiles_single_bounce_handoff_without_authority():
    declaration, baseline, gate = load_inputs()
    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    assert handoff.classification == "KY_VALIDATED_HANDOFF"
    assert handoff.task_id == declaration["task_id"]
    assert handoff.intended_action == {"operation": "deploy", "target": "preview"}
    assert handoff.validity == {"mode": "single_bounce", "runtime_state_bound": False}
    assert handoff.authority_granted is False


def test_non_pass_gate_cannot_compile_handoff():
    declaration, baseline, _ = load_inputs()
    declaration["recognized_hazards"] = []
    review = evaluate_ky_gate(declaration, baseline)
    assert review.outcome == "REVIEW"
    with pytest.raises(FreshHandoffError, match="requires KY Gate PASS"):
        compile_fresh_handoff(
            declaration, baseline, review, handoff_id="HANDOFF-PREVIEW-001"
        )


def test_mutated_declaration_after_pass_is_rejected():
    declaration, baseline, gate = load_inputs()
    declaration["intended_action"]["target"] = "production"
    with pytest.raises(FreshHandoffError, match="does not match deterministic evaluation"):
        compile_fresh_handoff(
            declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
        )


def test_mutated_baseline_after_pass_is_rejected():
    declaration, baseline, gate = load_inputs()
    baseline["required_hazard_ids"].append("new_hazard")
    with pytest.raises(FreshHandoffError, match="does not match deterministic evaluation"):
        compile_fresh_handoff(
            declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
        )


def test_forged_pass_result_is_rejected():
    declaration, baseline, gate = load_inputs()
    forged = replace(gate, baseline_fingerprint="sha256:forged")
    with pytest.raises(FreshHandoffError, match="does not match deterministic evaluation"):
        compile_fresh_handoff(
            declaration, baseline, forged, handoff_id="HANDOFF-PREVIEW-001"
        )


def test_handoff_uses_baseline_required_ids_not_worker_only_extras():
    declaration, baseline, gate = load_inputs()
    declaration["recognized_hazards"].append(
        {"id": "worker_only_hazard", "summary": "worker-only concern"}
    )
    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"
    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    assert "worker_only_hazard" not in handoff.required_hazard_ids
    assert handoff.required_hazard_ids == sorted(baseline["required_hazard_ids"])


def test_handoff_forbidden_scope_is_conservative_union():
    declaration, baseline, gate = load_inputs()
    declaration["understood_forbidden_scope"].append(
        {"operation": "delete", "target": "preview"}
    )
    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"
    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    assert {"operation": "delete", "target": "preview"} in handoff.forbidden_actions
    assert {"operation": "deploy", "target": "production"} in handoff.forbidden_actions


def test_handoff_excludes_previous_worker_reasoning_and_summaries():
    declaration, baseline, gate = load_inputs()
    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    dumped = json.dumps(asdict(handoff), sort_keys=True)
    assert "summary" not in dumped
    assert "declared_by" not in dumped
    assert "reasoning" not in dumped


def test_handoff_bindings_are_deterministic():
    declaration, baseline, gate = load_inputs()
    a = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    b = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )
    assert asdict(a) == asdict(b)


def test_handoff_does_not_forward_broader_allowed_scope():
    declaration, baseline, _ = load_inputs()
    extra = {"operation": "read", "target": "preview"}
    declaration["understood_allowed_scope"].append(extra)
    baseline["allowed_actions"].append(extra)
    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"

    handoff = compile_fresh_handoff(
        declaration, baseline, gate, handoff_id="HANDOFF-PREVIEW-001"
    )

    assert handoff.admitted_actions == [
        {"operation": "deploy", "target": "preview"}
    ]
    assert extra not in handoff.admitted_actions
