"""Fail-closed behaviour for malformed or fail-open policy bundles and awkward YAML inputs.

Each test here reproduces something that, before hardening, either crashed with an
unrelated exception, silently weakened a rule, or turned missing evidence into PASS.
"""
import copy
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from nazeyatta.evaluator import PolicyError, evaluate, load_yaml

ROOT = Path(__file__).resolve().parents[1]
POLICIES = load_yaml(ROOT / "policies/generic/rules.yaml")
PUBLISH = load_yaml(ROOT / "examples/publish-photo.yaml")
SAFE_READ = load_yaml(ROOT / "examples/safe-read.yaml")


def test_pass_is_not_an_allowed_policy_effect():
    # A policy must not be able to convert UNKNOWN evidence into PASS (fail-open).
    policies = copy.deepcopy(POLICIES)
    policies["rules"][3]["requires"][1]["on"] = {"unknown": "PASS", "default": "PASS"}
    with pytest.raises(PolicyError, match="effect must be one of"):
        evaluate(PUBLISH, policies)


def test_effect_typo_is_a_policy_error_not_keyerror():
    policies = copy.deepcopy(POLICIES)
    policies["rules"][3]["requires"][1]["on"] = {"unknown": "BLOCk"}
    with pytest.raises(PolicyError, match="BLOCk"):
        evaluate(PUBLISH, policies)


def test_unquoted_on_key_is_accepted_as_effect_map():
    # YAML 1.1 parses a bare `on:` key as boolean True. The bundle must keep its BLOCK.
    text = (ROOT / "policies/generic/rules.yaml").read_text(encoding="utf-8").replace('"on":', "on:")
    policies = yaml.safe_load(text)
    assert True in policies["rules"][3]["requires"][1]
    result = evaluate(PUBLISH, policies)
    assert result.outcome == "BLOCK"
    assert any(f["rule_id"] == "NY-PUB-001" and f["effect"] == "BLOCK" for f in result.findings)


def test_in_condition_must_be_a_list():
    policies = copy.deepcopy(POLICIES)
    policies["rules"][0]["when"]["all"][0]["in"] = "external_write"  # would substring-match "write"
    task = copy.deepcopy(SAFE_READ)
    task["action"]["side_effect"] = "write"
    with pytest.raises(PolicyError, match="must be a list"):
        evaluate(task, policies)


def test_unknown_when_selector_is_rejected():
    policies = copy.deepcopy(POLICIES)
    policies["rules"][0]["when"] = {"alll": [{"field": "action.side_effect", "equals": "destructive"}]}
    with pytest.raises(PolicyError, match="unsupported selector"):
        evaluate(SAFE_READ, policies)


def test_rule_missing_required_keys_is_rejected():
    policies = copy.deepcopy(POLICIES)
    del policies["rules"][3]["hazard"]
    with pytest.raises(PolicyError, match="missing required key"):
        evaluate(PUBLISH, policies)


def test_unquoted_yaml_timestamp_in_evidence_record_is_still_provenance_qualified():
    text = (ROOT / "examples/provenance-qualified-safe-read.yaml").read_text(encoding="utf-8")
    task = yaml.safe_load(text.replace('"2026-08-30T00:00:00+09:00"', "2026-08-30T00:00:00+09:00"))
    assert isinstance(task["evidence_records"]["EV-CAP-001"]["observed_at"], datetime)
    result = evaluate(task, POLICIES)
    assert result.outcome == "PASS"
    assert result.task_fingerprint.startswith("sha256:")


def test_naive_datetime_object_is_invalid():
    task = load_yaml(ROOT / "examples/provenance-qualified-safe-read.yaml")
    task["evidence_records"]["EV-CAP-001"]["observed_at"] = datetime(2026, 8, 30)
    result = evaluate(task, POLICIES)
    # NY-CAP-001 maps an INVALID record to BLOCK (stronger than the REVIEW used for MISSING).
    assert result.outcome == "BLOCK"
    assert result.findings[0]["evidence_state"] == "INVALID"


def test_date_values_in_policy_metadata_do_not_break_fingerprints():
    policies = copy.deepcopy(POLICIES)
    policies["policy_bundle"]["adopted"] = date(2026, 8, 30)
    a = evaluate(SAFE_READ, policies)
    b = evaluate(SAFE_READ, policies)
    assert a.policy_bundle_fingerprint == b.policy_bundle_fingerprint
    assert a.policy_bundle_fingerprint != evaluate(SAFE_READ, POLICIES).policy_bundle_fingerprint


def test_timezone_aware_datetime_object_passes():
    task = load_yaml(ROOT / "examples/provenance-qualified-safe-read.yaml")
    task["evidence_records"]["EV-CAP-001"]["observed_at"] = datetime(2026, 8, 30, tzinfo=timezone(timedelta(hours=9)))
    assert evaluate(task, POLICIES).outcome == "PASS"


def _cli(*args, env_extra=None):
    import os

    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=ROOT,
    )


def test_cli_require_lane_rejects_legacy_scalar_evidence():
    proc = _cli("check", "examples/safe-read.yaml", "--require-lane", "provenance-v0.2")
    assert proc.returncode == 2
    assert "LANE MISMATCH" in proc.stderr
    ok = _cli("check", "examples/provenance-qualified-safe-read.yaml", "--require-lane", "provenance-v0.2")
    assert ok.returncode == 0


def test_cli_reports_invalid_input_without_traceback(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    proc = _cli("check", str(bad))
    assert proc.returncode == 3
    assert "INVALID INPUT" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_survives_legacy_console_encoding():
    # Simulates a Windows console code page; the receipt must still print and exit 0.
    proc = _cli("check", "examples/safe-read.yaml", env_extra={"PYTHONIOENCODING": "cp932"})
    assert proc.returncode == 0, proc.stderr
    assert "PASS" in proc.stdout
