from pathlib import Path

from nazeyatta.evaluator import evaluate, load_yaml

ROOT = Path(__file__).resolve().parents[1]
POLICIES = load_yaml(ROOT / "policies/generic/rules.yaml")


def test_safe_read_passes():
    task = load_yaml(ROOT / "examples/safe-read.yaml")
    result = evaluate(task, POLICIES)
    assert result.outcome == "PASS"
    assert result.authority_granted is False


def test_unknown_publication_permission_blocks():
    task = load_yaml(ROOT / "examples/publish-photo.yaml")
    result = evaluate(task, POLICIES)
    assert result.outcome == "BLOCK"
    assert any(f["rule_id"] == "NY-PUB-001" for f in result.findings)


def test_unknown_liveness_blocks_delete():
    task = load_yaml(ROOT / "examples/destructive-delete.yaml")
    result = evaluate(task, POLICIES)
    assert result.outcome == "BLOCK"
    assert any(f["rule_id"] == "NY-LIVE-001" for f in result.findings)


def test_deterministic_receipt_fingerprints():
    task = load_yaml(ROOT / "examples/publish-photo.yaml")
    a = evaluate(task, POLICIES)
    b = evaluate(task, POLICIES)
    assert a.task_fingerprint == b.task_fingerprint
    assert a.policy_bundle_fingerprint == b.policy_bundle_fingerprint
    assert a.findings == b.findings


def test_packaged_policy_matches_public_policy():
    packaged = load_yaml(ROOT / "src/nazeyatta/data/generic_rules.yaml")
    assert packaged == POLICIES


def v02_safe_read(record: dict | None = None) -> dict:
    return {
        "schema_version": "0.2",
        "task_id": "TEST-V02-SAFE-READ",
        "action": {"operation": "read", "side_effect": "none", "externality": "internal"},
        "worker": {"required_capability": "read_repository"},
        "semantics": {"critical_meaning_complete": True},
        "evidence": {"worker_capability_qualified": "EV-CAP-001"},
        "evidence_records": {
            "EV-CAP-001": record or {
                "evidence_id": "EV-CAP-001",
                "supports_claim": "worker_capability_qualified",
                "observed_at": "2026-08-30T00:00:00+09:00",
                "observer": {"type": "human_or_adapter"},
                "verification": {"state": "VERIFIED"},
            }
        },
    }


def test_v02_provenance_qualified_evidence_passes():
    result = evaluate(v02_safe_read(), POLICIES)
    assert result.outcome == "PASS"
    assert result.evidence_lane == "provenance-v0.2"
    assert result.authority_granted is False


def test_v02_missing_referenced_record_does_not_pass():
    task = v02_safe_read()
    task["evidence_records"] = {}
    result = evaluate(task, POLICIES)
    assert result.outcome == "REVIEW"
    assert result.findings[0]["evidence_state"] == "MISSING"


def test_v02_claim_mismatch_is_invalid_not_verified():
    task = v02_safe_read()
    task["evidence_records"]["EV-CAP-001"]["supports_claim"] = "authority_verified"
    result = evaluate(task, POLICIES)
    assert result.outcome == "BLOCK"
    assert result.findings[0]["evidence_state"] == "INVALID"


def test_v02_record_id_mismatch_is_invalid_not_verified():
    task = v02_safe_read()
    task["evidence_records"]["EV-CAP-001"]["evidence_id"] = "EV-OTHER"
    result = evaluate(task, POLICIES)
    assert result.outcome == "BLOCK"
    assert result.findings[0]["evidence_state"] == "INVALID"


def test_v02_unknown_or_non_normalized_state_does_not_pass():
    task = v02_safe_read()
    task["evidence_records"]["EV-CAP-001"]["verification"]["state"] = "UNKNOWN"
    assert evaluate(task, POLICIES).outcome == "REVIEW"
    task["evidence_records"]["EV-CAP-001"]["verification"]["state"] = "verified"
    result = evaluate(task, POLICIES)
    assert result.outcome == "BLOCK"
    assert result.findings[0]["evidence_state"] == "INVALID"


def test_legacy_scalar_lane_is_compatible_but_not_provenance_qualified():
    result = evaluate(load_yaml(ROOT / "examples/safe-read.yaml"), POLICIES)
    assert result.outcome == "PASS"
    assert result.evidence_lane == "legacy-v0.1"
