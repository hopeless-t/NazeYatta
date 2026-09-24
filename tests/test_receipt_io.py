import json
import subprocess
import sys
from pathlib import Path

import pytest

from nazeyatta.evaluator import evaluate, load_yaml
from nazeyatta.receipt_io import deterministic_receipt_json, write_receipt_json

ROOT = Path(__file__).resolve().parents[1]
POLICIES = load_yaml(ROOT / "policies/generic/rules.yaml")


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )


def test_deterministic_receipt_json_is_stable_and_newline_terminated():
    receipt = evaluate(load_yaml(ROOT / "examples/safe-read.yaml"), POLICIES)
    a = deterministic_receipt_json(receipt)
    b = deterministic_receipt_json(receipt)

    assert a == b
    assert a.endswith("\n")
    assert a.startswith('{"authority_granted":false,')
    payload = json.loads(a)
    assert payload["outcome"] == "PASS"
    assert payload["authority_granted"] is False


def test_write_receipt_json_refuses_to_overwrite(tmp_path):
    receipt = evaluate(load_yaml(ROOT / "examples/safe-read.yaml"), POLICIES)
    target = tmp_path / "receipt.json"

    write_receipt_json(receipt, target)
    original = target.read_bytes()

    with pytest.raises(FileExistsError):
        write_receipt_json(receipt, target)

    assert target.read_bytes() == original


def test_cli_receipt_out_writes_pass_receipt(tmp_path):
    target = tmp_path / "pass.json"
    proc = _cli("check", "examples/safe-read.yaml", "--receipt-out", str(target))

    assert proc.returncode == 0
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["outcome"] == "PASS"
    assert payload["authority_granted"] is False


def test_cli_receipt_out_writes_non_pass_receipt(tmp_path):
    target = tmp_path / "block.json"
    proc = _cli("check", "examples/publish-photo.yaml", "--receipt-out", str(target))

    assert proc.returncode == 2
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["outcome"] == "BLOCK"
    assert payload["authority_granted"] is False


def test_cli_receipt_out_refuses_existing_file(tmp_path):
    target = tmp_path / "receipt.json"
    target.write_text("DO NOT REPLACE\n", encoding="utf-8")

    proc = _cli("check", "examples/safe-read.yaml", "--receipt-out", str(target))

    assert proc.returncode == 3
    assert "RECEIPT WRITE FAILED" in proc.stderr
    assert target.read_text(encoding="utf-8") == "DO NOT REPLACE\n"


def test_lane_mismatch_does_not_emit_receipt_file(tmp_path):
    target = tmp_path / "receipt.json"

    proc = _cli(
        "check",
        "examples/safe-read.yaml",
        "--require-lane",
        "provenance-v0.2",
        "--receipt-out",
        str(target),
    )

    assert proc.returncode == 2
    assert "LANE MISMATCH" in proc.stderr
    assert not target.exists()
