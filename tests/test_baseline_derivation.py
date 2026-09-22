from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import shutil

import pytest

from nazeyatta.baseline_derivation import (
    BaselineDerivationError,
    validate_baseline_derivation,
)
from nazeyatta.evaluator import load_yaml, stable_hash
from nazeyatta.runtime_fixture_sources import observe_fixture_sources

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TEMPLATE = ROOT / "tests" / "fixtures" / "source-observation"
BASELINE_PATH = ROOT / "examples" / "ky-baseline-safe-read-runtime.yaml"


def observe(source_root: Path, baseline: dict):
    refs = baseline["source_refs"]
    return observe_fixture_sources(
        manifest_path=source_root / "manifest.json",
        source_root=source_root,
        authority_ref=refs["authority_ref"],
        policy_ref=refs["policy_ref"],
        evidence_refs=list(refs["evidence_refs"]),
    )


def record_for(baseline: dict, snapshots: dict) -> dict:
    return {
        "schema_version": "0.1",
        "derivation_id": "DERIVATION-DOGFOOD-001",
        "classification": "BASELINE_DERIVATION_RECORD",
        "task_id": baseline["task_id"],
        "baseline_id": baseline["baseline_id"],
        "baseline_fingerprint": stable_hash(baseline),
        "source_snapshots": snapshots,
        "prepared_by": {
            "type": "human",
            "identifier": "dogfood-fixture-authority",
        },
        "derivation_method": {
            "type": "manual",
            "identifier": "dogfood-safe-read-baseline-preparation",
            "version": "0.1",
        },
        "prepared_at": datetime(2026, 9, 22, tzinfo=timezone.utc).isoformat(),
        "semantic_correctness_claimed": False,
        "authority_granted": False,
    }


def test_record_binds_exact_baseline_and_observed_source_snapshots(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)

    result = validate_baseline_derivation(
        baseline,
        record,
        current_source_snapshots=snapshots,
    )

    assert result.outcome == "PROVENANCE_BOUND"
    assert result.findings == []
    assert result.semantic_correctness_verified is False
    assert result.authority_granted is False


def test_changed_baseline_rejects_old_derivation_record(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)

    baseline["required_hazard_ids"].append("new_hazard")

    with pytest.raises(BaselineDerivationError, match="fingerprint"):
        validate_baseline_derivation(baseline, record)


def test_changed_policy_source_marks_record_stale(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    before = observe(source_root, baseline)
    record = record_for(baseline, before)

    policy_path = source_root / "policy.json"
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    after = observe(source_root, baseline)

    result = validate_baseline_derivation(
        baseline,
        record,
        current_source_snapshots=after,
    )

    assert result.outcome == "SOURCE_CHANGED"
    assert any(f["code"] == "POLICY_SOURCE_CHANGED" for f in result.findings)


def test_changed_evidence_state_marks_source_changed(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    before = observe(source_root, baseline)
    record = record_for(baseline, before)

    evidence_path = source_root / "evidence.json"
    import json
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    payload["state"] = "STALE"
    evidence_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    after = observe(source_root, baseline)

    result = validate_baseline_derivation(
        baseline,
        record,
        current_source_snapshots=after,
    )

    codes = {f["code"] for f in result.findings}
    assert result.outcome == "SOURCE_CHANGED"
    assert "EVIDENCE_SOURCE_CHANGED" in codes
    assert "EVIDENCE_STATE_CHANGED" in codes


def test_record_source_refs_must_exactly_match_baseline(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)
    record["source_snapshots"]["policy_binding"]["ref"] = "policy://dogfood/other"

    with pytest.raises(BaselineDerivationError, match="policy ref"):
        validate_baseline_derivation(baseline, record)


def test_record_requires_observed_source_snapshots(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)
    record["source_snapshots"]["authority_binding"]["observation_state"] = "CARRIED_FORWARD"

    with pytest.raises(BaselineDerivationError, match="must be OBSERVED"):
        validate_baseline_derivation(baseline, record)


def test_record_cannot_claim_semantic_correctness(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)
    record["semantic_correctness_claimed"] = True

    with pytest.raises(BaselineDerivationError, match="semantic_correctness_claimed"):
        validate_baseline_derivation(baseline, record)


def test_record_cannot_grant_authority(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)
    record["authority_granted"] = True

    with pytest.raises(BaselineDerivationError, match="authority_granted"):
        validate_baseline_derivation(baseline, record)


def test_result_is_deterministic(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)

    a = validate_baseline_derivation(baseline, record, current_source_snapshots=snapshots)
    b = validate_baseline_derivation(baseline, record, current_source_snapshots=snapshots)

    assert asdict(a) == asdict(b)


def test_non_baseline_object_is_rejected_even_if_ids_and_refs_exist(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)

    invalid = {
        "schema_version": "0.1",
        "baseline_id": baseline["baseline_id"],
        "task_id": baseline["task_id"],
        "classification": "NOT_A_BASELINE",
        "source_refs": deepcopy(baseline["source_refs"]),
    }

    with pytest.raises(BaselineDerivationError):
        validate_baseline_derivation(invalid, record)


def test_extra_baseline_field_is_rejected(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    baseline = load_yaml(BASELINE_PATH)
    snapshots = observe(source_root, baseline)
    record = record_for(baseline, snapshots)

    baseline["unexpected_derivation_magic"] = True

    with pytest.raises(BaselineDerivationError, match="unsupported keys"):
        validate_baseline_derivation(baseline, record)
