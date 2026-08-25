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
