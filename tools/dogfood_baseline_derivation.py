from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "tests" / "fixtures" / "source-observation"

sys.path.insert(0, str(ROOT / "src"))

from nazeyatta.baseline_derivation import validate_baseline_derivation
from nazeyatta.evaluator import stable_hash


AUTHORITY_REF = "authority://dogfood/ci-safe-read-only"
POLICY_REF = "policy://dogfood/runtime-safe-read-v0-1"
EVIDENCE_REF = "evidence://dogfood/fixture-exists"


def _read_json_fixture(name: str) -> tuple[dict, str]:
    path = SOURCE_ROOT / name
    payload = path.read_bytes()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{name} must contain a JSON object")
    token = "sha256:" + hashlib.sha256(payload).hexdigest()
    return data, token


def main() -> int:
    authority, authority_token = _read_json_fixture("authority.json")
    policy, policy_token = _read_json_fixture("policy.json")
    evidence, evidence_token = _read_json_fixture("evidence.json")

    if authority.get("classification") != "DOGFOOD_AUTHORITY_FIXTURE":
        raise RuntimeError("unexpected authority fixture classification")
    if policy.get("classification") != "DOGFOOD_POLICY_FIXTURE":
        raise RuntimeError("unexpected policy fixture classification")
    if evidence.get("classification") != "DOGFOOD_EVIDENCE_FIXTURE":
        raise RuntimeError("unexpected evidence fixture classification")

    allowed_action = authority.get("allowed_action")
    if not isinstance(allowed_action, dict) or set(allowed_action) != {"operation", "target"}:
        raise RuntimeError("authority fixture allowed_action is malformed")

    target = policy.get("target")
    allowed_operation = policy.get("allowed_operation")
    forbidden_operations = policy.get("forbidden_operations")
    if not isinstance(target, str) or not target:
        raise RuntimeError("policy fixture target is malformed")
    if not isinstance(allowed_operation, str) or not allowed_operation:
        raise RuntimeError("policy fixture allowed_operation is malformed")
    if not isinstance(forbidden_operations, list) or not all(
        isinstance(op, str) and op for op in forbidden_operations
    ):
        raise RuntimeError("policy fixture forbidden_operations is malformed")

    if target != allowed_action["target"]:
        raise RuntimeError("authority and policy fixture targets disagree")
    if allowed_operation != allowed_action["operation"]:
        raise RuntimeError("authority and policy fixture allowed operations disagree")
    if allowed_operation in forbidden_operations:
        raise RuntimeError("policy fixture both allows and forbids the same operation")

    evidence_state = evidence.get("state")
    if evidence_state not in {
        "VERIFIED",
        "PRESENT",
        "STALE",
        "INVALID",
        "MISSING",
        "UNKNOWN",
    }:
        raise RuntimeError("evidence fixture state is invalid")
    if evidence.get("target") != target:
        raise RuntimeError("evidence and policy fixture targets disagree")

    now = datetime.now(timezone.utc).isoformat()
    baseline = {
        "schema_version": "0.1",
        "baseline_id": "KY-BASELINE-DERIVATION-DOGFOOD-001",
        "task_id": "DOGFOOD-BASELINE-DERIVATION-001",
        "classification": "NORMALIZED_VALIDATION_BASELINE",
        "allowed_actions": [
            {
                "operation": allowed_action["operation"],
                "target": allowed_action["target"],
            }
        ],
        "forbidden_actions": [
            {"operation": operation, "target": target}
            for operation in forbidden_operations
        ],
        # The current fixtures do not define KY hazard/control/stop semantics.
        # Do not invent requirements that are absent from the sources.
        "required_hazard_ids": [],
        "required_control_ids": [],
        "required_stop_condition_ids": [],
        "source_refs": {
            "authority_ref": AUTHORITY_REF,
            "policy_ref": POLICY_REF,
            "evidence_refs": [EVIDENCE_REF],
        },
        "prepared_by": {
            "type": "workflow",
            "identifier": "dogfood-baseline-derivation-tool",
        },
        "prepared_at": now,
    }

    snapshots = {
        "authority_binding": {
            "ref": AUTHORITY_REF,
            "observation_state": "OBSERVED",
            "binding_token": authority_token,
        },
        "policy_binding": {
            "ref": POLICY_REF,
            "observation_state": "OBSERVED",
            "binding_token": policy_token,
        },
        "evidence_bindings": [
            {
                "ref": EVIDENCE_REF,
                "observation_state": "OBSERVED",
                "state": evidence_state,
                "binding_token": evidence_token,
            }
        ],
    }

    record = {
        "schema_version": "0.1",
        "derivation_id": "DERIVATION-DOGFOOD-001",
        "classification": "BASELINE_DERIVATION_RECORD",
        "task_id": baseline["task_id"],
        "baseline_id": baseline["baseline_id"],
        "baseline_fingerprint": stable_hash(baseline),
        "source_snapshots": snapshots,
        "prepared_by": {
            "type": "workflow",
            "identifier": "dogfood-baseline-derivation-tool",
        },
        "derivation_method": {
            "type": "deterministic_adapter",
            "identifier": "dogfood-fixture-baseline-transform",
            "version": "0.1",
        },
        "prepared_at": now,
        "semantic_correctness_claimed": False,
        "authority_granted": False,
    }

    result = validate_baseline_derivation(
        baseline,
        record,
        current_source_snapshots=snapshots,
    )
    if result.outcome != "PROVENANCE_BOUND":
        raise RuntimeError(
            f"derivation dogfood expected PROVENANCE_BOUND, got {result.outcome}"
        )

    summary = {
        "dogfood": "PASS",
        "classification": "BASELINE_DERIVATION_DOGFOOD",
        "derivation_outcome": result.outcome,
        "baseline_fingerprint": result.baseline_fingerprint,
        "record_fingerprint": result.record_fingerprint,
        "source_snapshots_observed": True,
        "derivation_method": "dogfood-fixture-baseline-transform@0.1",
        "derived_required_hazard_ids": [],
        "derived_required_control_ids": [],
        "derived_required_stop_condition_ids": [],
        "semantic_correctness_verified": result.semantic_correctness_verified,
        "authority_granted": result.authority_granted,
        "production_baseline_compiler_claimed": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
