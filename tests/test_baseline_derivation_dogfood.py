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
