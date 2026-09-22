from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

from nazeyatta.evaluator import load_yaml
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"


def compiled_handoff() -> dict:
    declaration = load_yaml(ROOT / "examples/worker-ky-safe-read-runtime.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-safe-read-runtime.yaml")
    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"
    return asdict(
        compile_fresh_handoff(
            declaration,
            baseline,
            gate,
            handoff_id="HANDOFF-DOGFOOD-SAFE-READ-TEST",
        )
    )


def run_worker(tmp_path: Path, payload: dict, allowed_root: Path = FIXTURE_ROOT):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    env = {
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONNOUSERSITE": "1",
    }
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "nazeyatta.runtime_safe_read",
            "--handoff",
            str(handoff_path),
            "--allowed-root",
            str(allowed_root),
        ],
        cwd=allowed_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )


def test_runtime_dogfood_orchestrator_runs_fresh_process():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "dogfood_safe_read.py")],
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
    assert summary["classification"] == "PARTIAL_RUNTIME_DOGFOOD"
    assert summary["fresh_process"] is True
    assert summary["parent_pid"] != summary["worker_pid"]
    assert summary["operation"] == "read"
    assert summary["target"] == "runtime-dogfood.txt"
    assert summary["target_identity_unchanged"] is True
    assert summary["authority_granted"] is False
    assert summary["source_bindings_observed"] is False
    assert summary["reky_runtime_evaluated"] is True
    assert summary["reky_runtime_outcome"] == "RE_KY"
    assert {
        "AUTHORITY_NOT_OBSERVED",
        "POLICY_NOT_OBSERVED",
        "EVIDENCE_NOT_OBSERVED",
    } <= set(summary["reky_reason_codes"])
    assert summary["full_reky_runtime_continuation_claimed"] is False
    assert "This file is intentionally boring" not in proc.stdout


def test_safe_read_worker_receipt_contains_digest_not_contents(tmp_path):
    proc = run_worker(tmp_path, compiled_handoff())
    assert proc.returncode == 0, proc.stderr
    receipt = json.loads(proc.stdout)
    fixture = (FIXTURE_ROOT / "runtime-dogfood.txt").read_bytes()
    assert receipt["bytes_read"] == len(fixture)
    assert receipt["content_sha256"].startswith("sha256:")
    assert "NazeYatta runtime dogfood fixture" not in proc.stdout
    assert receipt["authority_granted"] is False
    assert receipt["worker_pid"] != os.getpid()


def test_safe_read_worker_rejects_write_operation(tmp_path):
    payload = compiled_handoff()
    payload["intended_action"]["operation"] = "write"
    payload["admitted_actions"][0]["operation"] = "write"
    proc = run_worker(tmp_path, payload)
    assert proc.returncode == 3
    assert "accepts only operation='read'" in proc.stderr


def test_safe_read_worker_rejects_parent_escape(tmp_path):
    payload = compiled_handoff()
    payload["intended_action"]["target"] = "../pyproject.toml"
    payload["admitted_actions"][0]["target"] = "../pyproject.toml"
    proc = run_worker(tmp_path, payload)
    assert proc.returncode == 3
    assert "stay beneath the allowed root" in proc.stderr


def test_safe_read_worker_rejects_symlink_escape(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (allowed / "link.txt").symlink_to(outside)

    payload = compiled_handoff()
    payload["intended_action"]["target"] = "link.txt"
    payload["admitted_actions"][0]["target"] = "link.txt"
    proc = run_worker(tmp_path, payload, allowed_root=allowed)
    assert proc.returncode == 3
    assert "escapes the allowed root" in proc.stderr


def test_safe_read_worker_rejects_extra_handoff_fields(tmp_path):
    payload = compiled_handoff()
    payload["previous_worker_reasoning"] = "should never be accepted"
    proc = run_worker(tmp_path, payload)
    assert proc.returncode == 3
    assert "unsupported keys" in proc.stderr
