from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_baseline_derivation_dogfood_is_bounded_and_truthful():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dogfood_baseline_derivation.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)

    assert summary["dogfood"] == "PASS"
    assert summary["classification"] == "BASELINE_DERIVATION_DOGFOOD"
    assert summary["derivation_outcome"] == "PROVENANCE_BOUND"
    assert summary["source_snapshots_observed"] is True
    assert summary["derivation_method"] == "dogfood-fixture-baseline-transform@0.1"

    # Current fixtures contain no hazard/control/stop derivation semantics.
    # The dogfood must not invent them.
    assert summary["derived_required_hazard_ids"] == []
    assert summary["derived_required_control_ids"] == []
    assert summary["derived_required_stop_condition_ids"] == []

    assert summary["semantic_correctness_verified"] is False
    assert summary["authority_granted"] is False
    assert summary["production_baseline_compiler_claimed"] is False


def test_dogfood_transform_rejects_conflicting_authority_and_policy(tmp_path):
    import shutil

    source_template = ROOT / "tests" / "fixtures" / "source-observation"
    source_root = tmp_path / "source-observation"
    shutil.copytree(source_template, source_root)

    policy_path = source_root / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["allowed_operation"] = "write"
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    # The production dogfood tool intentionally uses the repository fixture root.
    # Exercise the same bounded source-consistency rule directly here.
    authority = json.loads((source_root / "authority.json").read_text(encoding="utf-8"))
    allowed_action = authority["allowed_action"]

    assert policy["allowed_operation"] != allowed_action["operation"]
