from pathlib import Path
import subprocess
import sys

import pytest

from nazeyatta.cli import default_policy_path, packaged_example_path
from nazeyatta.evaluator import evaluate, load_yaml


ROOT = Path(__file__).resolve().parents[1]

CASES = {
    "publish-photo": ("examples/publish-photo.yaml", "BLOCK"),
    "safe-read": ("examples/safe-read.yaml", "PASS"),
}


@pytest.mark.parametrize("name, expected", CASES.items())
def test_packaged_example_matches_repository_example(name, expected):
    repository_path, _ = expected
    assert packaged_example_path(name).read_bytes() == (ROOT / repository_path).read_bytes()


@pytest.mark.parametrize("name, expected", CASES.items())
def test_example_command_prints_exact_yaml(name, expected):
    repository_path, _ = expected
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "example", name],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
    assert proc.stdout == (ROOT / repository_path).read_text(encoding="utf-8")
    assert "NAZEYATTA" not in proc.stdout


@pytest.mark.parametrize("name, expected", CASES.items())
def test_packaged_example_keeps_existing_check_semantics(name, expected):
    _, expected_outcome = expected
    task = load_yaml(packaged_example_path(name))
    policies = load_yaml(default_policy_path())

    receipt = evaluate(task, policies)

    assert receipt.outcome == expected_outcome
    assert receipt.authority_granted is False


def test_example_command_rejects_unknown_name():
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "example", "../other"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr
