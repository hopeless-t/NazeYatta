from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "tests" / "fixtures" / "source-observation"
SPEC_PATH = ROOT / "examples" / "dogfood-baseline-derivation-spec.json"
ADOPTION_RECORD_PATH = ROOT / "examples" / "dogfood-spec-adoption-record.json"

sys.path.insert(0, str(ROOT / "src"))

from nazeyatta.baseline_derivation import validate_baseline_derivation
from nazeyatta.evaluator import stable_hash
from nazeyatta.spec_adoption import evaluate_spec_adoption


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


def _load_spec() -> tuple[dict, str]:
    payload = SPEC_PATH.read_bytes()
    spec = json.loads(payload.decode("utf-8"))
    if not isinstance(spec, dict):
        raise RuntimeError("derivation spec must be a JSON object")

    expected_top = {
        "schema_version",
        "spec_id",
        "classification",
        "version",
        "source_classifications",
        "mapping",
        "semantic_correctness_claimed",
        "authority_granted",
    }
    if set(spec) != expected_top:
        raise RuntimeError("derivation spec has unsupported or missing top-level fields")
    if spec["schema_version"] != "0.1":
        raise RuntimeError("unsupported derivation spec schema_version")
    if spec["spec_id"] != "dogfood-fixture-baseline-transform":
        raise RuntimeError("unsupported derivation spec id")
    if spec["classification"] != "DOGFOOD_BASELINE_DERIVATION_SPEC":
        raise RuntimeError("unexpected derivation spec classification")
    if spec["version"] != "0.1":
        raise RuntimeError("unsupported derivation spec version")
    if spec["semantic_correctness_claimed"] is not False:
        raise RuntimeError("derivation spec must not claim semantic correctness")
    if spec["authority_granted"] is not False:
        raise RuntimeError("derivation spec must not grant authority")

    expected_classes = {
        "authority": "DOGFOOD_AUTHORITY_FIXTURE",
        "policy": "DOGFOOD_POLICY_FIXTURE",
        "evidence": "DOGFOOD_EVIDENCE_FIXTURE",
    }
    if spec["source_classifications"] != expected_classes:
        raise RuntimeError("unsupported source classifications in derivation spec")

    expected_mapping = {
        "allowed_actions_from": "authority.allowed_action",
        "forbidden_operations_from": "policy.forbidden_operations",
        "forbidden_target_from": "policy.target",
        "required_hazard_ids": [],
        "required_control_ids": [],
        "required_stop_condition_ids": [],
    }
    if spec["mapping"] != expected_mapping:
        raise RuntimeError("unsupported mapping in derivation spec")

    return spec, "sha256:" + hashlib.sha256(payload).hexdigest()


def _load_adoption_record() -> dict:
    record = json.loads(ADOPTION_RECORD_PATH.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise RuntimeError("spec adoption record must be a JSON object")
    return record


def main() -> int:
    spec, spec_file_sha256 = _load_spec()
    adoption_record = _load_adoption_record()
    now = datetime.now(timezone.utc).isoformat()

    expected_scope = {
        "task_id": "DOGFOOD-BASELINE-DERIVATION-001",
        "authority_source_ref": AUTHORITY_REF,
        "policy_source_ref": POLICY_REF,
        "evidence_source_refs": [EVIDENCE_REF],
    }
    adoption = evaluate_spec_adoption(
        spec,
        adoption_record,
        expected_scope=expected_scope,
        evaluated_at=now,
    )
    if adoption.outcome != "RECORD_BOUND":
        raise RuntimeError(
            f"dogfood spec adoption record is not admissible: "
            f"{adoption.outcome} {adoption.findings!r}"
        )

    authority, authority_token = _read_json_fixture("authority.json")
    policy, policy_token = _read_json_fixture("policy.json")
    evidence, evidence_token = _read_json_fixture("evidence.json")

    classes = spec["source_classifications"]
    if authority.get("classification") != classes["authority"]:
        raise RuntimeError("unexpected authority fixture classification")
    if policy.get("classification") != classes["policy"]:
        raise RuntimeError("unexpected policy fixture classification")
    if evidence.get("classification") != classes["evidence"]:
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
        "derivation_method": f"{spec['spec_id']}@{spec['version']}",
        "derivation_spec_fingerprint": stable_hash(spec),
        "derivation_spec_file_sha256": spec_file_sha256,
        "spec_adoption_outcome": adoption.outcome,
        "spec_adoption_record_fingerprint": adoption.record_fingerprint,
        "spec_authority_authenticated": adoption.authority_authenticated,
        "spec_normative_correctness_verified": adoption.normative_correctness_verified,
        "transform_conforms_to_declared_spec": True,
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
