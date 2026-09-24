from copy import deepcopy
from pathlib import Path

import pytest

from nazeyatta.evaluator import evaluate, load_yaml, stable_hash
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.preflight_runtime_correlation import build_preflight_runtime_correlation
from nazeyatta.reky_gate import build_boundary_observation


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies/generic/rules.yaml"

CASES = [
    "examples/release-github-publication-v02.synthetic.yaml",
    "examples/release-pypi-publication-v02.synthetic.yaml",
]


def _synthetic_pass_task(path: str):
    task = deepcopy(load_yaml(ROOT / path))
    task["evidence_records"]["EV-AUTH"]["verification"]["state"] = "VERIFIED"
    task["evidence_records"]["EV-PERM"]["verification"]["state"] = "VERIFIED"
    return task


def _project_release_target(task):
    descriptor = task["action"]["target"]
    provider = descriptor["provider"]
    fingerprint = stable_hash(descriptor)
    digest = fingerprint.removeprefix("sha256:")
    target_token = f"{provider}-publication:{digest}"
    assert len(target_token) <= 128
    return target_token, fingerprint


def _ky_handoff_for_task(task):
    target_token, _ = _project_release_target(task)
    action = {"operation": task["action"]["operation"], "target": target_token}

    declaration = {
        "schema_version": "0.2",
        "declaration_id": f"KY-{task['task_id']}",
        "task_id": task["task_id"],
        "classification": "WORKER_SELF_REPORT",
        "intended_action": action,
        "understood_allowed_scope": [action],
        "understood_forbidden_scope": [],
        "recognized_hazards": [],
        "planned_controls": [],
        "stop_conditions": [],
        "declared_by": {"type": "worker", "identifier": "synthetic-release-worker"},
        "declared_at": "2026-09-24T19:50:00+09:00",
    }

    evidence_refs = [
        f"evidence://release/{evidence_id.lower()}"
        for evidence_id in sorted(task["evidence_records"])
    ]
    baseline = {
        "schema_version": "0.1",
        "baseline_id": f"BASELINE-{task['task_id']}",
        "task_id": task["task_id"],
        "classification": "NORMALIZED_VALIDATION_BASELINE",
        "allowed_actions": [action],
        "forbidden_actions": [],
        "required_hazard_ids": [],
        "required_control_ids": [],
        "required_stop_condition_ids": [],
        "source_refs": {
            "authority_ref": "authority://release/synthetic-human-gate",
            "policy_ref": "policy://nazeyatta/generic-v0.1",
            "evidence_refs": evidence_refs,
        },
        "prepared_by": {"type": "adapter", "identifier": "synthetic-release-mapper"},
        "prepared_at": "2026-09-24T19:50:00+09:00",
    }

    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"
    handoff = compile_fresh_handoff(
        declaration,
        baseline,
        gate,
        handoff_id=f"HANDOFF-{task['task_id']}",
    )
    return handoff


def _source_snapshot(task, policies, handoff):
    records = task["evidence_records"]
    refs = list(handoff.source_refs["evidence_refs"])
    record_ids = sorted(records)
    assert len(refs) == len(record_ids)

    return {
        "authority_binding": {
            "ref": handoff.source_refs["authority_ref"],
            "observation_state": "OBSERVED",
            "binding_token": stable_hash(records["EV-AUTH"]),
        },
        "policy_binding": {
            "ref": handoff.source_refs["policy_ref"],
            "observation_state": "OBSERVED",
            "binding_token": stable_hash(policies),
        },
        "evidence_bindings": [
            {
                "ref": ref,
                "observation_state": "OBSERVED",
                "state": records[evidence_id]["verification"]["state"],
                "binding_token": stable_hash(records[evidence_id]),
            }
            for ref, evidence_id in zip(refs, record_ids, strict=True)
        ],
    }


def _observation_for_task(task, policies, handoff):
    target_token, target_fingerprint = _project_release_target(task)
    return build_boundary_observation(
        handoff,
        observation_id=f"OBS-{task['task_id']}",
        target_binding={
            "kind": f"{task['action']['target']['provider']}_release",
            "identifier": target_token,
            "identity_fingerprint": target_fingerprint,
        },
        source_snapshot=_source_snapshot(task, policies, handoff),
        observed_by={"type": "adapter", "identifier": "synthetic-release-mapper"},
        observed_at="2026-09-24T19:50:01+09:00",
    )


def _assert_consumer_target_mapping(task, handoff, observation):
    target_token, target_fingerprint = _project_release_target(task)
    expected_action = {
        "operation": task["action"]["operation"],
        "target": target_token,
    }
    if handoff.intended_action != expected_action:
        raise ValueError("preflight Task target does not map to FreshHandoff intended target")
    if observation["target_binding"]["identifier"] != target_token:
        raise ValueError("runtime target identifier does not map to preflight Task target")
    if observation["target_binding"]["identity_fingerprint"] != target_fingerprint:
        raise ValueError("runtime target fingerprint does not map to preflight Task target")


@pytest.mark.parametrize("fixture", CASES)
def test_explicit_release_projection_binds_task_handoff_and_observation_without_promoting_claims(fixture):
    task = _synthetic_pass_task(fixture)
    policies = load_yaml(POLICY)
    receipt = evaluate(task, policies)
    assert receipt.outcome == "PASS"

    handoff = _ky_handoff_for_task(task)
    observation = _observation_for_task(task, policies, handoff)
    _assert_consumer_target_mapping(task, handoff, observation)

    record = build_preflight_runtime_correlation(
        receipt, task, policies, handoff, observation
    )

    _, expected_fingerprint = _project_release_target(task)
    assert record.target_binding["identity_fingerprint"] == expected_fingerprint
    assert record.correlation_outcome == "EXACT_ARTIFACTS_BOUND"
    assert record.semantic_equivalence_verified is False
    assert record.freshness_verified is False
    assert record.authority_granted is False


@pytest.mark.parametrize("fixture", CASES)
def test_generic_correlation_does_not_claim_semantic_equivalence_when_task_target_drifts(fixture):
    original = _synthetic_pass_task(fixture)
    policies = load_yaml(POLICY)
    handoff = _ky_handoff_for_task(original)
    observation = _observation_for_task(original, policies, handoff)

    drifted = deepcopy(original)
    target = drifted["action"]["target"]
    if target["provider"] == "github":
        target["tag"] = "v9.9.9-synthetic-drift"
    else:
        target["version"] = "9.9.9-synthetic-drift"

    drifted_receipt = evaluate(drifted, policies)
    assert drifted_receipt.outcome == "PASS"
    assert drifted_receipt.task_fingerprint != evaluate(original, policies).task_fingerprint

    record = build_preflight_runtime_correlation(
        drifted_receipt, drifted, policies, handoff, observation
    )

    assert record.correlation_outcome == "EXACT_ARTIFACTS_BOUND"
    assert record.semantic_equivalence_verified is False
    assert record.freshness_verified is False
    assert record.authority_granted is False

    with pytest.raises(ValueError, match="does not map"):
        _assert_consumer_target_mapping(drifted, handoff, observation)
