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
    assert summary["derivation_spec_fingerprint"] == "sha256:bdceeb42ad5924f25794c2451af5a378e49503d2df4c6ff688fb74c67de361ba"
    assert summary["derivation_spec_file_sha256"] == "sha256:57418f0193edd4410bf20ba5c7c62f7e60b3eb290306bd274d547f16227784a0"
    assert summary["spec_adoption_outcome"] == "RECORD_BOUND"
    assert summary["spec_adoption_record_fingerprint"].startswith("sha256:")
    assert summary["spec_authority_authenticated"] is False
    assert summary["spec_normative_correctness_verified"] is False
    assert summary["transform_conforms_to_declared_spec"] is True

    # Current fixtures contain no hazard/control/stop derivation semantics.
    # The dogfood must not invent them.
    assert summary["derived_required_hazard_ids"] == []
    assert summary["derived_required_control_ids"] == []
    assert summary["derived_required_stop_condition_ids"] == []

    assert summary["semantic_correctness_verified"] is False
    assert summary["authority_granted"] is False
    assert summary["production_baseline_compiler_claimed"] is False


def test_dogfood_transform_rejects_conflicting_authority_and_policy(tmp_path):
    import importlib.util
    import shutil

    source_template = ROOT / "tests" / "fixtures" / "source-observation"
    source_root = tmp_path / "source-observation"
    shutil.copytree(source_template, source_root)

    policy_path = source_root / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["allowed_operation"] = "write"
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    tool_path = ROOT / "tools" / "dogfood_baseline_derivation.py"
    spec = importlib.util.spec_from_file_location(
        "dogfood_baseline_derivation_test_module",
        tool_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE_ROOT = source_root

    import pytest
    with pytest.raises(RuntimeError, match="allowed operations disagree"):
        module.main()


def test_dogfood_transform_rejects_unsupported_mapping_spec(tmp_path):
    import importlib.util

    tool_path = ROOT / "tools" / "dogfood_baseline_derivation.py"
    spec_obj = importlib.util.spec_from_file_location(
        "dogfood_baseline_derivation_spec_test_module",
        tool_path,
    )
    assert spec_obj is not None and spec_obj.loader is not None
    module = importlib.util.module_from_spec(spec_obj)
    spec_obj.loader.exec_module(module)

    spec_path = tmp_path / "spec.json"
    spec = json.loads(
        (ROOT / "examples" / "dogfood-baseline-derivation-spec.json").read_text(
            encoding="utf-8"
        )
    )
    spec["mapping"]["allowed_actions_from"] = "policy.magic"
    spec_path.write_text(json.dumps(spec) + "\n", encoding="utf-8")
    module.SPEC_PATH = spec_path

    import pytest
    with pytest.raises(RuntimeError, match="unsupported mapping"):
        module.main()


def test_dogfood_rejects_revoked_spec_adoption_record(tmp_path):
    import importlib.util

    tool_path = ROOT / "tools" / "dogfood_baseline_derivation.py"
    spec_obj = importlib.util.spec_from_file_location(
        "dogfood_baseline_derivation_revoked_adoption_test_module",
        tool_path,
    )
    assert spec_obj is not None and spec_obj.loader is not None
    module = importlib.util.module_from_spec(spec_obj)
    spec_obj.loader.exec_module(module)

    record_path = tmp_path / "adoption.json"
    record = json.loads(
        (ROOT / "examples" / "dogfood-spec-adoption-record.json").read_text(
            encoding="utf-8"
        )
    )
    record["status"] = "REVOKED"
    record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    module.ADOPTION_RECORD_PATH = record_path

    import pytest
    with pytest.raises(RuntimeError, match="not admissible"):
        module.main()
