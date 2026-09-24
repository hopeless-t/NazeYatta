from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nazeyatta.evaluator import evaluate, load_yaml, stable_hash
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.preflight_runtime_correlation import build_preflight_runtime_correlation
from nazeyatta.reky_gate import build_boundary_observation


TASK_ID = "DOGFOOD-FIRST-PARTY-GITHUB-RELEASE-001"

# Historical, already-published target from Issue #94.
# This script never calls GitHub or performs an external write.
RELEASE_INTENT = {
    "kind": "github_release",
    "repository": "hopeless-t/NazeYatta",
    "tag": "v0.2.0a3",
    "target_commit": "16b7b0ae5ba0c7e8dcd7e728dd6808a43c5095e8",
    "wheel_sha256": "38662971bb43314d0df795d84c34e9f03d60cc69ac5b165596cc4e393c5c8242",
    "sdist_sha256": "875b36fc4d5cfe90af49624d8236b383a9e1b7e85f30e30e541761095e2667be",
}


def target_identifier(intent: dict[str, str]) -> str:
    return (
        f"github-release:{intent['repository']}:{intent['tag']}"
        f"@{intent['target_commit']}"
    )


def target_binding(intent: dict[str, str]) -> dict[str, str]:
    return {
        "kind": "github_release",
        "identifier": target_identifier(intent),
        "identity_fingerprint": stable_hash(intent),
    }


def assert_target_binding_matches_intent(
    intent: dict[str, str],
    binding: dict[str, str],
) -> None:
    expected = target_binding(intent)
    if binding != expected:
        raise RuntimeError("target binding does not exactly match adapter-owned Release Intent")


def build_preflight_task(intent: dict[str, str]) -> dict:
    # The generic Task keeps only generic action semantics.
    # Exact target identity remains adapter-owned and is carried by the KY/runtime lane.
    _ = intent
    return {
        "task_id": TASK_ID,
        "action": {
            "operation": "publish",
            "side_effect": "external_write",
            "externality": "public",
        },
        "semantics": {"critical_meaning_complete": True},
        "evidence": {
            "authority_verified": "VERIFIED",
            "execution_target_verified": "VERIFIED",
            "provenance_verified": "VERIFIED",
            "publication_permission_verified": "VERIFIED",
            "evidence_bundle_current": "VERIFIED",
        },
    }


def build_ky_inputs(intent: dict[str, str]) -> tuple[dict, dict]:
    target = target_identifier(intent)

    hazards = [
        {"id": "wrong_release_target", "summary": "publish to a different repository, tag, or commit"},
        {"id": "artifact_drift", "summary": "publish artifacts whose hashes differ from the verified release intent"},
        {"id": "authority_unknown", "summary": "publish without the separate Human release gate"},
    ]
    controls = [
        {"id": "exact_target_binding", "summary": "derive the handoff target from the exact release intent"},
        {"id": "exact_artifact_hashes", "summary": "retain the verified wheel and sdist hashes in the release intent"},
        {"id": "human_release_gate", "summary": "keep publication authority outside NazeYatta"},
    ]
    stops = [
        {"id": "target_mismatch", "summary": "derived repository, tag, or commit differs from the intent"},
        {"id": "hash_mismatch", "summary": "artifact hash differs from the intent"},
        {"id": "authority_not_established", "summary": "the separate Human publication gate is not established"},
    ]

    declaration = {
        "schema_version": "0.2",
        "declaration_id": "KY-DOGFOOD-FIRST-PARTY-RELEASE-001",
        "task_id": TASK_ID,
        "classification": "WORKER_SELF_REPORT",
        "intended_action": {"operation": "publish", "target": target},
        "understood_allowed_scope": [{"operation": "publish", "target": target}],
        "understood_forbidden_scope": [],
        "recognized_hazards": hazards,
        "planned_controls": controls,
        "stop_conditions": stops,
        "declared_by": {"type": "worker", "identifier": "release-mapping-dry-run"},
        "declared_at": "2026-09-24T10:20:40+00:00",
    }

    baseline = {
        "schema_version": "0.1",
        "baseline_id": "KY-BASELINE-FIRST-PARTY-RELEASE-001",
        "task_id": TASK_ID,
        "classification": "NORMALIZED_VALIDATION_BASELINE",
        "allowed_actions": [{"operation": "publish", "target": target}],
        "forbidden_actions": [],
        "required_hazard_ids": [item["id"] for item in hazards],
        "required_control_ids": [item["id"] for item in controls],
        "required_stop_condition_ids": [item["id"] for item in stops],
        "source_refs": {
            "authority_ref": "authority://human/release-publication-gate",
            "policy_ref": "policy://nazeyatta/generic-v0.1",
            "evidence_refs": ["evidence://release/v0.2.0a3/historical-readback"],
        },
        "prepared_by": {"type": "human", "identifier": "historical-release-fixture"},
        "prepared_at": "2026-09-24T10:20:40+00:00",
    }
    return declaration, baseline


def carried_forward_source_snapshot(handoff) -> dict:
    return {
        "authority_binding": {
            "ref": handoff.source_refs["authority_ref"],
            "observation_state": "CARRIED_FORWARD",
            "binding_token": None,
        },
        "policy_binding": {
            "ref": handoff.source_refs["policy_ref"],
            "observation_state": "CARRIED_FORWARD",
            "binding_token": None,
        },
        "evidence_bindings": [
            {
                "ref": ref,
                "observation_state": "CARRIED_FORWARD",
                "state": "UNKNOWN",
                "binding_token": None,
            }
            for ref in handoff.source_refs["evidence_refs"]
        ],
    }


def main() -> int:
    intent = deepcopy(RELEASE_INTENT)
    binding = target_binding(intent)
    assert_target_binding_matches_intent(intent, binding)

    task = build_preflight_task(intent)
    policies = load_yaml(ROOT / "policies" / "generic" / "rules.yaml")
    receipt = evaluate(task, policies)
    if receipt.outcome != "PASS":
        raise RuntimeError(f"historical release preflight fixture did not PASS: {receipt.outcome}")
    if receipt.authority_granted is not False:
        raise RuntimeError("preflight receipt must not grant authority")

    declaration, baseline = build_ky_inputs(intent)
    gate = evaluate_ky_gate(declaration, baseline)
    if gate.outcome != "PASS":
        raise RuntimeError(f"release mapping KY Gate did not PASS: {gate.outcome}")

    handoff = compile_fresh_handoff(
        declaration,
        baseline,
        gate,
        handoff_id="HANDOFF-DOGFOOD-FIRST-PARTY-RELEASE-001",
    )

    if task["action"]["operation"] != handoff.intended_action["operation"]:
        raise RuntimeError("adapter-generated preflight operation and handoff operation diverged")
    if handoff.intended_action["target"] != binding["identifier"]:
        raise RuntimeError("adapter-generated handoff target and exact target binding diverged")
    assert_target_binding_matches_intent(intent, binding)

    observation = build_boundary_observation(
        handoff,
        observation_id="OBS-DOGFOOD-FIRST-PARTY-RELEASE-001",
        target_binding=binding,
        source_snapshot=carried_forward_source_snapshot(handoff),
        observed_by={
            "type": "workflow",
            "identifier": "first-party-release-mapping-dry-run",
        },
        observed_at="2026-09-24T10:20:40+00:00",
    )

    correlation = build_preflight_runtime_correlation(
        receipt,
        task,
        policies,
        handoff,
        observation,
    )
    if correlation.correlation_outcome != "EXACT_ARTIFACTS_BOUND":
        raise RuntimeError(f"unexpected correlation outcome: {correlation.correlation_outcome}")
    if correlation.target_binding != binding:
        raise RuntimeError("correlation record target binding differs from adapter binding")
    if correlation.semantic_equivalence_verified is not False:
        raise RuntimeError("dry-run must not claim generic semantic equivalence")
    if correlation.freshness_verified is not False:
        raise RuntimeError("historical fixture must not claim freshness")
    if correlation.authority_granted is not False:
        raise RuntimeError("correlation must not grant authority")

    mutation_checks = {}
    for field, replacement in (
        ("tag", "v0.2.0a4"),
        ("target_commit", "73366b80576927ac15ca1cc961d066cfe17de214"),
    ):
        mutated = deepcopy(intent)
        mutated[field] = replacement
        try:
            assert_target_binding_matches_intent(mutated, binding)
        except RuntimeError:
            mutation_checks[field] = "REJECTED"
        else:
            raise RuntimeError(f"mutated {field} unexpectedly matched original target binding")

    summary = {
        "dogfood": "PASS",
        "classification": "FIRST_PARTY_RELEASE_MAPPING_DRY_RUN",
        "task_id": TASK_ID,
        "operation": task["action"]["operation"],
        "side_effect": task["action"]["side_effect"],
        "externality": task["action"]["externality"],
        "target_identifier": binding["identifier"],
        "target_identity_fingerprint": binding["identity_fingerprint"],
        "adapter_generated_operation_consistent": True,
        "adapter_generated_target_consistent": True,
        "mutation_checks": mutation_checks,
        "ky_outcome": gate.outcome,
        "preflight_outcome": receipt.outcome,
        "correlation_outcome": correlation.correlation_outcome,
        "correlation_semantic_equivalence_verified": False,
        "correlation_freshness_verified": False,
        "authority_authenticated": False,
        "authority_granted": False,
        "external_write_performed": False,
        "network_mutation_performed": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
