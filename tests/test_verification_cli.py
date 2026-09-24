from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml

from nazeyatta.evaluator import stable_hash


ROOT = Path(__file__).resolve().parents[1]


def _fp(label: str) -> str:
    return stable_hash({"label": label})


def _payloads():
    request = {
        "schema_version": "0.1",
        "classification": "POST_ACTION_VERIFICATION_REQUEST",
        "verification_id": "CUTE-001",
        "task_id": "DEPLOY-001",
        "preflight_receipt_fingerprint": _fp("preflight"),
        "task_fingerprint": _fp("task"),
        "action_fingerprint": _fp("action"),
        "target_binding": {
            "kind": "deployment",
            "identifier": "preview",
            "identity_fingerprint": _fp("target"),
        },
        "expected_facts": {"production_touched": False},
        "authority_granted": False,
    }
    observation = {
        "schema_version": "0.1",
        "classification": "POST_ACTION_OBSERVATION",
        "observation_id": "OBS-CUTE-001",
        "verification_id": "CUTE-001",
        "task_id": "DEPLOY-001",
        "preflight_receipt_fingerprint": _fp("preflight"),
        "task_fingerprint": _fp("task"),
        "action_fingerprint": _fp("action"),
        "target_binding": dict(request["target_binding"]),
        "observed_facts": {
            "production_touched": {
                "observation_state": "OBSERVED",
                "value": True,
            }
        },
        "observed_by": {"type": "workflow", "identifier": "cute-test"},
        "observed_at": "2026-09-25T00:00:00+09:00",
        "authority_granted": False,
    }
    return request, observation


def _write(tmp_path: Path, request: dict, observation: dict):
    request_path = tmp_path / "request.yaml"
    observation_path = tmp_path / "observation.yaml"
    request_path.write_text(yaml.safe_dump(request, sort_keys=False), encoding="utf-8")
    observation_path.write_text(yaml.safe_dump(observation, sort_keys=False), encoding="utf-8")
    return request_path, observation_path


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", *map(str, args)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_verify_human_projection_is_playful_but_unambiguous(tmp_path):
    request, observation = _payloads()
    rp, op = _write(tmp_path, request, observation)

    proc = _run("verify", rp, op)

    assert proc.returncode == 2
    assert "🙀" in proc.stdout
    assert "NAZE YATTA?" in proc.stdout
    assert "VERIFIED_FAILURE" in proc.stdout
    assert "production_touched" in proc.stdout
    assert "expected: false" in proc.stdout
    assert "observed: true" in proc.stdout
    assert "EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA" in proc.stdout
    assert "RETRY AUTHORITY: NOT GRANTED BY NAZEYATTA" in proc.stdout


def test_verify_json_projection_stays_machine_neutral(tmp_path):
    request, observation = _payloads()
    rp, op = _write(tmp_path, request, observation)

    proc = _run("verify", rp, op, "--json")

    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["outcome"] == "VERIFIED_FAILURE"
    assert payload["authority_granted"] is False
    assert payload["retry_authorized"] is False
    assert "NAZE YATTA" not in proc.stdout


def test_verify_success_exit_zero(tmp_path):
    request, observation = _payloads()
    observation["observed_facts"]["production_touched"]["value"] = False
    rp, op = _write(tmp_path, request, observation)

    proc = _run("verify", rp, op)

    assert proc.returncode == 0
    assert "✅😺 VERIFIED_SUCCESS" in proc.stdout


def test_verify_unknown_exit_two(tmp_path):
    request, observation = _payloads()
    observation["observed_facts"]["production_touched"] = {
        "observation_state": "UNKNOWN",
        "value": None,
    }
    rp, op = _write(tmp_path, request, observation)

    proc = _run("verify", rp, op)

    assert proc.returncode == 2
    assert "🔎😿 UNKNOWN" in proc.stdout


def test_verify_binding_mismatch_is_invalid_input_exit_three(tmp_path):
    request, observation = _payloads()
    observation["task_id"] = "WRONG"
    rp, op = _write(tmp_path, request, observation)

    proc = _run("verify", rp, op)

    assert proc.returncode == 3
    assert "INVALID VERIFICATION INPUT" in proc.stderr


def test_verify_receipt_out_is_no_clobber(tmp_path):
    request, observation = _payloads()
    observation["observed_facts"]["production_touched"]["value"] = False
    rp, op = _write(tmp_path, request, observation)
    target = tmp_path / "receipt.json"

    first = _run("verify", rp, op, "--receipt-out", target)
    assert first.returncode == 0
    assert json.loads(target.read_text(encoding="utf-8"))["outcome"] == "VERIFIED_SUCCESS"

    second = _run("verify", rp, op, "--receipt-out", target)
    assert second.returncode == 3
    assert "RECEIPT WRITE FAILED" in second.stderr
