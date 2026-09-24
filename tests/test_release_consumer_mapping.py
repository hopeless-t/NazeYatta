from copy import deepcopy
from pathlib import Path

import pytest

from nazeyatta.evaluator import evaluate, load_yaml


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies/generic/rules.yaml"

CASES = [
    ("examples/release-github-publication-v02.synthetic.yaml", "github"),
    ("examples/release-pypi-publication-v02.synthetic.yaml", "pypi"),
]


@pytest.mark.parametrize("fixture, provider", CASES)
def test_release_mapping_fixtures_are_v02_and_fail_closed_without_human_authority(fixture, provider):
    task = load_yaml(ROOT / fixture)
    receipt = evaluate(task, load_yaml(POLICY))

    assert task["schema_version"] == "0.2"
    assert task["action"]["target"]["provider"] == provider
    assert task["data"]["fixture_only"] is True
    assert receipt.evidence_lane == "provenance-v0.2"
    assert receipt.outcome == "BLOCK"
    assert receipt.authority_granted is False

    blocked_claims = {
        finding["evidence_key"]
        for finding in receipt.findings
        if finding["effect"] == "BLOCK"
    }
    assert "authority_verified" in blocked_claims
    assert "publication_permission_verified" in blocked_claims


@pytest.mark.parametrize("fixture, provider", CASES)
def test_synthetic_human_verified_variant_can_pass_but_never_grants_execution_authority(fixture, provider):
    task = deepcopy(load_yaml(ROOT / fixture))
    task["evidence_records"]["EV-AUTH"]["verification"]["state"] = "VERIFIED"
    task["evidence_records"]["EV-PERM"]["verification"]["state"] = "VERIFIED"

    receipt = evaluate(task, load_yaml(POLICY))

    assert task["action"]["target"]["provider"] == provider
    assert receipt.outcome == "PASS"
    assert receipt.authority_granted is False
    assert receipt.evidence_lane == "provenance-v0.2"
