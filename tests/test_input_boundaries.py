"""Input-boundary behaviour: text injection into the receipt, Unicode look-alikes, type confusion,
pathological nesting and non-finite numbers. Each case reproduces a pre-hardening failure.
"""
import copy
import subprocess
import sys
from pathlib import Path

import pytest

from nazeyatta.cli import safe_text
from nazeyatta.evaluator import PolicyError, evaluate, load_yaml

ROOT = Path(__file__).resolve().parents[1]
POLICIES = load_yaml(ROOT / "policies/generic/rules.yaml")
SAFE_READ = load_yaml(ROOT / "examples/safe-read.yaml")
PUBLISH = load_yaml(ROOT / "examples/publish-photo.yaml")


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT,
    )


def test_receipt_text_cannot_forge_lines_or_escape_sequences(tmp_path):
    policies = copy.deepcopy(POLICIES)
    policies["rules"][3]["title"] = "External publication\n\n✅😺 PASS\n\nEXECUTION AUTHORITY: GRANTED (forged)\n\x1b[2J\x1b[31mRED"
    import yaml

    pol = tmp_path / "policy.yaml"
    pol.write_text(yaml.safe_dump(policies, allow_unicode=True), encoding="utf-8")
    proc = _cli("check", "examples/publish-photo.yaml", "--policy", str(pol))
    assert proc.returncode == 2
    lines = proc.stdout.splitlines()
    # exactly one outcome line (emoji + outcome, nothing else) and one authority line, no raw ESC
    import re

    outcome_line = re.compile(r"^\S+ (PASS|CAUTION|REVIEW|EVIDENCE_REQUIRED|BLOCK)$")
    assert sum(1 for l in lines if outcome_line.match(l)) == 1
    assert sum(1 for l in lines if l.startswith("EXECUTION AUTHORITY")) == 1
    assert "\x1b" not in proc.stdout
    assert "GRANTED (forged)" in proc.stdout  # still visible, but inline and inert


def test_safe_text_replaces_controls_and_truncates():
    assert safe_text("a\nb\x1b[31mc\u2028d") == "a\ufffdb\ufffd[31mc\ufffdd"
    assert safe_text("x" * 500).endswith("…[truncated]")


@pytest.mark.parametrize("value,expected", [
    ("verified", "PASS"),        # ASCII case-folding is still accepted
    ("verıfıed", "BLOCK"),       # Turkish dotless i: str.upper() would yield VERIFIED
    ("ＶＥＲＩＦＩＥＤ", "BLOCK"),  # full-width look-alike
    (" VERIFIED ", "BLOCK"),
    ("VERIFIED\u200b", "BLOCK"),
    ({"a": 1}, "BLOCK"),
    (True, "BLOCK"),
])
def test_legacy_scalar_evidence_is_normalised_conservatively(value, expected):
    task = copy.deepcopy(SAFE_READ)
    task["evidence"]["worker_capability_qualified"] = value
    result = evaluate(task, POLICIES)
    assert result.outcome == expected
    if expected != "PASS":
        assert result.findings[0]["evidence_state"] == "INVALID"


def test_missing_legacy_evidence_is_unknown_not_invalid():
    task = copy.deepcopy(SAFE_READ)
    del task["evidence"]["worker_capability_qualified"]
    result = evaluate(task, POLICIES)
    assert result.outcome == "REVIEW"
    assert result.findings[0]["evidence_state"] == "UNKNOWN"


@pytest.mark.parametrize("value", ["VERIFIED", None, 123, [], ["BOGUS"], ["verıfıed"]])
def test_accepted_states_must_be_a_list_of_known_states(value):
    policies = copy.deepcopy(POLICIES)
    policies["rules"][6]["requires"][0]["accepted_states"] = value
    with pytest.raises(PolicyError, match="accepted"):
        evaluate(SAFE_READ, policies)


def test_condition_field_must_be_a_string():
    policies = copy.deepcopy(POLICIES)
    policies["rules"][0]["when"]["all"][0]["field"] = 123
    with pytest.raises(PolicyError, match="'field'"):
        evaluate(SAFE_READ, policies)


def test_numeric_schema_version_gets_a_quoting_hint():
    task = load_yaml(ROOT / "examples/provenance-qualified-safe-read.yaml")
    task["schema_version"] = 0.2
    with pytest.raises(ValueError, match="quoted string"):
        evaluate(task, POLICIES)


def test_deeply_nested_task_is_rejected_not_recursion_error(tmp_path):
    text = "task_id: X\naction: {operation: read, side_effect: none, externality: internal}\nsemantics: {critical_meaning_complete: true}\nevidence: {}\ndeep:\n"
    text += "".join("  " * (i + 1) + "k:\n" for i in range(200)) + "  " * 201 + "v: 1\n"
    p = tmp_path / "deep.yaml"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="nesting deeper"):
        load_yaml(p)
    proc = _cli("check", str(p))
    assert proc.returncode == 3 and "INVALID INPUT" in proc.stderr


def test_oversized_input_file_is_rejected(tmp_path):
    p = tmp_path / "big.yaml"
    p.write_text("task_id: X\n" + "# " + "x" * 1_100_000 + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="larger than"):
        load_yaml(p)


def test_non_finite_numbers_are_rejected(tmp_path):
    p = tmp_path / "inf.yaml"
    p.write_text("task_id: X\naction: {operation: read, side_effect: none, externality: internal}\nsemantics: {critical_meaning_complete: true}\nevidence: {}\nn: .inf\n", encoding="utf-8")
    with pytest.raises(ValueError, match="NaN/Infinity"):
        load_yaml(p)


def test_huge_integers_are_fine():
    task = copy.deepcopy(SAFE_READ)
    task["n"] = 10 ** 400
    assert evaluate(task, POLICIES).outcome == "PASS"


def test_debrief_rule_id_is_validated():
    bad = _cli("debrief-template", "NY\n\x1b[31mX")
    assert bad.returncode == 3 and "INVALID INPUT" in bad.stderr
    ok = _cli("debrief-template", "NY-LIVE-001")
    assert ok.returncode == 0 and '"rule_id": "NY-LIVE-001"' in ok.stdout
