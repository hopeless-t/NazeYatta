from copy import deepcopy
from dataclasses import asdict, fields, replace
import json
from pathlib import Path

import pytest

from nazeyatta.evaluator import evaluate, load_yaml, stable_hash
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.preflight_runtime_correlation import (
    PreflightRuntimeCorrelationError,
    PreflightRuntimeCorrelationRecord,
    build_preflight_runtime_correlation,
)
from nazeyatta.reky_gate import (
    ObservationGateError,
    build_boundary_observation,
    validate_boundary_observation_for_handoff,
)

ROOT = Path(__file__).resolve().parents[1]


def _context():
    declaration = load_yaml(ROOT / "examples/worker-ky-preview.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-preview.yaml")
    gate = evaluate_ky_gate(declaration, baseline)
    handoff = compile_fresh_handoff(
        declaration,
        baseline,
        gate,
        handoff_id="HANDOFF-CORRELATION-TEST",
    )

    before = load_yaml(ROOT / "examples/boundary-before.yaml")
    source_snapshot = {
        "authority_binding": before["authority_binding"],
        "policy_binding": before["policy_binding"],
        "evidence_bindings": before["evidence_bindings"],
    }
    observation = build_boundary_observation(
        handoff,
        observation_id="OBS-CORRELATION-001",
        target_binding=before["target_binding"],
        source_snapshot=source_snapshot,
        observed_by=before["observed_by"],
        observed_at=before["observed_at"],
    )

    task = {
        "task_id": handoff.task_id,
        "action": {
            "operation": "deploy",
            "side_effect": "external_write",
            "externality": "internal",
        },
        "semantics": {"critical_meaning_complete": True},
        "evidence": {
            "authority_verified": "VERIFIED",
            "execution_target_verified": "VERIFIED",
            "evidence_bundle_current": "VERIFIED",
        },
    }
    policies = load_yaml(ROOT / "policies/generic/rules.yaml")
    receipt = evaluate(task, policies)
    assert receipt.outcome == "PASS"

    return task, policies, receipt, handoff, observation


def test_correlation_record_binds_exact_artifacts_without_claiming_freshness():
    task, policies, receipt, handoff, observation = _context()

    record = build_preflight_runtime_correlation(
        receipt,
        task,
        policies,
        handoff,
        observation,
    )

    assert record.classification == "PREFLIGHT_RUNTIME_CORRELATION"
    assert record.task_id == task["task_id"] == handoff.task_id
    assert record.receipt_fingerprint == stable_hash(asdict(receipt))
    assert record.task_fingerprint == receipt.task_fingerprint
    assert record.policy_bundle_fingerprint == receipt.policy_bundle_fingerprint
    assert record.handoff_fingerprint == observation["handoff_fingerprint"]
    assert record.boundary_observation_fingerprint == stable_hash(observation)
    assert record.target_binding == observation["target_binding"]
    assert record.observed_at == observation["observed_at"]
    assert record.correlation_outcome == "EXACT_ARTIFACTS_BOUND"
    assert record.semantic_equivalence_verified is False
    assert record.freshness_verified is False
    assert record.authority_granted is False


def test_correlation_record_is_deterministic_for_same_artifacts():
    task, policies, receipt, handoff, observation = _context()

    a = build_preflight_runtime_correlation(
        receipt, task, policies, handoff, observation
    )
    b = build_preflight_runtime_correlation(
        receipt, task, policies, handoff, observation
    )

    assert asdict(a) == asdict(b)
    assert stable_hash(asdict(a)) == stable_hash(asdict(b))


def test_forged_receipt_is_rejected():
    task, policies, receipt, handoff, observation = _context()
    forged = replace(receipt, outcome="BLOCK")

    with pytest.raises(
        PreflightRuntimeCorrelationError,
        match="receipt does not exactly match",
    ):
        build_preflight_runtime_correlation(
            forged, task, policies, handoff, observation
        )


def test_different_preflight_task_id_is_rejected():
    task, policies, _, handoff, observation = _context()
    other_task = deepcopy(task)
    other_task["task_id"] = "OTHER-TASK"
    other_receipt = evaluate(other_task, policies)

    with pytest.raises(
        PreflightRuntimeCorrelationError,
        match="preflight task_id does not correlate",
    ):
        build_preflight_runtime_correlation(
            other_receipt,
            other_task,
            policies,
            handoff,
            observation,
        )


def test_observation_not_bound_to_handoff_is_rejected():
    task, policies, receipt, handoff, observation = _context()
    forged = deepcopy(observation)
    forged["target_binding"]["identifier"] = "production"

    with pytest.raises(
        PreflightRuntimeCorrelationError,
        match="boundary observation does not bind",
    ):
        build_preflight_runtime_correlation(
            receipt, task, policies, handoff, forged
        )


def test_public_observation_validator_rejects_forged_handoff_fingerprint():
    _, _, _, handoff, observation = _context()
    forged = deepcopy(observation)
    forged["handoff_fingerprint"] = "sha256:forged"

    with pytest.raises(ObservationGateError, match="does not bind to handoff"):
        validate_boundary_observation_for_handoff(handoff, forged)


def test_correlation_schema_matches_dataclass_and_non_claims():
    schema = json.loads(
        (
            ROOT / "schemas/preflight-runtime-correlation.schema.json"
        ).read_text(encoding="utf-8")
    )
    field_names = {field.name for field in fields(PreflightRuntimeCorrelationRecord)}

    assert set(schema["required"]) == field_names
    assert set(schema["properties"]) == field_names
    props = schema["properties"]
    assert props["schema_version"]["const"] == "0.1"
    assert props["classification"]["const"] == "PREFLIGHT_RUNTIME_CORRELATION"
    assert props["correlation_outcome"]["const"] == "EXACT_ARTIFACTS_BOUND"
    assert props["semantic_equivalence_verified"]["const"] is False
    assert props["freshness_verified"]["const"] is False
    assert props["authority_granted"]["const"] is False
