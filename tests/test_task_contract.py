import copy
import subprocess
import sys
from pathlib import Path

import pytest

from nazeyatta.evaluator import evaluate, load_yaml

ROOT = Path(__file__).resolve().parents[1]
POLICIES = load_yaml(ROOT / "policies/generic/rules.yaml")
SAFE_READ = load_yaml(ROOT / "examples/safe-read.yaml")
V02_SAFE_READ = load_yaml(ROOT / "examples/provenance-qualified-safe-read.yaml")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda task: task.pop("task_id"), "task_id"),
        (lambda task: task.pop("action"), "action"),
        (lambda task: task["action"].pop("operation"), "action.operation"),
        (lambda task: task["action"].pop("side_effect"), "action.side_effect"),
        (lambda task: task["action"].pop("externality"), "action.externality"),
        (lambda task: task.__setitem__("action", []), "action"),
        (lambda task: task["action"].__setitem__("operation", ""), "action.operation"),
        (lambda task: task["action"].__setitem__("side_effect", "maybe"), "action.side_effect"),
        (lambda task: task["action"].__setitem__("externality", "somewhere"), "action.externality"),
        (lambda task: task.pop("semantics"), "semantics"),
        (
            lambda task: task["semantics"].pop("critical_meaning_complete"),
            "semantics.critical_meaning_complete",
        ),
        (
            lambda task: task["semantics"].__setitem__("critical_meaning_complete", "false"),
            "semantics.critical_meaning_complete",
        ),
        (lambda task: task.__setitem__("worker", "self-declared"), "worker"),
        (lambda task: task.__setitem__("data", "private-ish"), "data"),
    ],
)
def test_structurally_incomplete_task_is_invalid_input(mutation, message):
    task = copy.deepcopy(SAFE_READ)
    mutation(task)

    with pytest.raises(ValueError, match=message):
        evaluate(task, POLICIES)


def test_v02_requires_evidence_records_mapping_even_before_rule_resolution():
    task = copy.deepcopy(V02_SAFE_READ)
    task.pop("evidence_records")

    with pytest.raises(ValueError, match="evidence_records"):
        evaluate(task, POLICIES)


def test_cli_reports_incomplete_task_as_invalid_input(tmp_path):
    task = tmp_path / "incomplete.yaml"
    task.write_text("task_id: INCOMPLETE\nevidence: {}\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "check", str(task)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )

    assert proc.returncode == 3
    assert "INVALID INPUT" in proc.stderr
    assert "action must be a mapping" in proc.stderr
