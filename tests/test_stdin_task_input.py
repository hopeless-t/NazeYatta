import json
from pathlib import Path
import subprocess
import sys

from nazeyatta.evaluator import MAX_INPUT_BYTES


ROOT = Path(__file__).resolve().parents[1]


def _check_stdin(payload: str, *args: str):
    return subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "check", "-", *args],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )


def test_safe_read_from_stdin_keeps_pass_semantics():
    payload = (ROOT / "examples/safe-read.yaml").read_text(encoding="utf-8")
    proc = _check_stdin(payload)

    assert proc.returncode == 0
    assert "PASS" in proc.stdout
    assert "EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA" in proc.stdout


def test_publish_photo_from_stdin_keeps_block_semantics():
    payload = (ROOT / "examples/publish-photo.yaml").read_text(encoding="utf-8")
    proc = _check_stdin(payload)

    assert proc.returncode == 2
    assert "BLOCK" in proc.stdout
    assert "publication_permission_verified = UNKNOWN" in proc.stdout
    assert "EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA" in proc.stdout


def test_stdin_json_receipt_is_machine_readable_and_non_authorizing():
    payload = (ROOT / "examples/safe-read.yaml").read_text(encoding="utf-8")
    proc = _check_stdin(payload, "--json")

    assert proc.returncode == 0
    receipt = json.loads(proc.stdout)
    assert receipt["outcome"] == "PASS"
    assert receipt["authority_granted"] is False
    assert receipt["evaluator_version"] == "1.1.0.dev0"


def test_packaged_example_output_can_feed_stdin_check():
    example = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "example", "safe-read"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        check=True,
    )
    proc = _check_stdin(example.stdout)

    assert proc.returncode == 0
    assert "PASS" in proc.stdout


def test_stdin_over_size_limit_fails_closed_before_evaluation():
    payload = b"#" * (MAX_INPUT_BYTES + 1)
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "check", "-"],
        input=payload,
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == 3
    assert b"INVALID INPUT" in proc.stderr
    assert b"input larger than" in proc.stderr


def test_stdin_non_utf8_fails_closed():
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "check", "-"],
        input=b"\xff\xfe\x00",
        capture_output=True,
        cwd=ROOT,
    )

    assert proc.returncode == 3
    assert b"INVALID INPUT" in proc.stderr
    assert b"not valid UTF-8" in proc.stderr


def test_policy_stdin_is_explicitly_rejected():
    payload = (ROOT / "examples/safe-read.yaml").read_text(encoding="utf-8")
    proc = _check_stdin(payload, "--policy", "-")

    assert proc.returncode == 3
    assert "--policy - is not supported" in proc.stderr
