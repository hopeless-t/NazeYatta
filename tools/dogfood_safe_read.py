from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
SOURCE_ROOT = FIXTURE_ROOT / "source-observation"
SOURCE_MANIFEST = SOURCE_ROOT / "manifest.json"

sys.path.insert(0, str(ROOT / "src"))

from nazeyatta.evaluator import load_yaml, stable_hash
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.reky_gate import evaluate_reky_gate
from nazeyatta.runtime_fixture_sources import observe_fixture_sources


def _observe_sources(handoff) -> dict:
    return observe_fixture_sources(
        manifest_path=SOURCE_MANIFEST,
        source_root=SOURCE_ROOT,
        authority_ref=handoff.source_refs["authority_ref"],
        policy_ref=handoff.source_refs["policy_ref"],
        evidence_refs=list(handoff.source_refs["evidence_refs"]),
    )


def main() -> int:
    declaration = load_yaml(ROOT / "examples" / "worker-ky-safe-read-runtime.yaml")
    baseline = load_yaml(ROOT / "examples" / "ky-baseline-safe-read-runtime.yaml")

    gate = evaluate_ky_gate(declaration, baseline)
    if gate.outcome != "PASS":
        raise RuntimeError(f"dogfood KY Gate did not PASS: {gate.outcome}")

    handoff = compile_fresh_handoff(
        declaration,
        baseline,
        gate,
        handoff_id="HANDOFF-DOGFOOD-SAFE-READ-001",
    )
    handoff_payload = asdict(handoff)
    handoff_fingerprint = stable_hash(handoff_payload)

    before_sources = _observe_sources(handoff)
    before_time = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory(prefix="nazeyatta-dogfood-") as td:
        handoff_path = Path(td) / "handoff.json"
        handoff_path.write_text(
            json.dumps(handoff_payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )

        env = {
            "PYTHONPATH": str(ROOT / "src"),
            "PYTHONNOUSERSITE": "1",
        }
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "nazeyatta.runtime_safe_read",
                "--handoff",
                str(handoff_path),
                "--allowed-root",
                str(FIXTURE_ROOT),
            ],
            cwd=FIXTURE_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )

    after_sources = _observe_sources(handoff)
    after_time = datetime.now(timezone.utc)

    if proc.returncode != 0:
        raise RuntimeError(
            "fresh safe-read subprocess failed: "
            f"rc={proc.returncode} stderr={proc.stderr.strip()!r}"
        )

    receipt = json.loads(proc.stdout)
    if receipt["handoff_fingerprint"] != handoff_fingerprint:
        raise RuntimeError("runtime receipt does not bind to compiled handoff")
    if receipt["worker_pid"] == os.getpid():
        raise RuntimeError("dogfood did not execute in a fresh subprocess")
    if receipt["operation"] != "read":
        raise RuntimeError("runtime receipt operation is not read")
    if receipt["target"] != "runtime-dogfood.txt":
        raise RuntimeError("runtime receipt target mismatch")
    if receipt["outcome"] != "READ_OK":
        raise RuntimeError(f"runtime read outcome was {receipt['outcome']!r}")
    if receipt["authority_granted"] is not False:
        raise RuntimeError("runtime receipt must not grant authority")
    if not receipt["target_identity_unchanged"]:
        raise RuntimeError("target identity changed during safe-read dogfood")

    common = {
        "schema_version": "0.2",
        "classification": "BOUNDARY_OBSERVATION",
        "task_id": handoff.task_id,
        "handoff_fingerprint": handoff_fingerprint,
        "observed_by": {
            "type": "workflow",
            "identifier": "dogfood-safe-read-orchestrator",
        },
    }
    before = {
        **common,
        "observation_id": "DOGFOOD-BOUNDARY-BEFORE",
        "target_binding": {
            "kind": "file",
            "identifier": receipt["target"],
            "identity_fingerprint": receipt[
                "before_target_identity_fingerprint"
            ],
        },
        **before_sources,
        "observed_at": before_time.isoformat(),
    }
    after = {
        **common,
        "observation_id": "DOGFOOD-BOUNDARY-AFTER",
        "target_binding": {
            "kind": "file",
            "identifier": receipt["target"],
            "identity_fingerprint": receipt[
                "after_target_identity_fingerprint"
            ],
        },
        **after_sources,
        "observed_at": after_time.isoformat(),
    }

    reky = evaluate_reky_gate(handoff, before, after)
    if reky.outcome != "CONTINUE":
        raise RuntimeError(
            f"fixture-source dogfood expected CONTINUE, got {reky.outcome}: {reky.reasons!r}"
        )
    reason_codes = sorted({reason["code"] for reason in reky.reasons})
    if reason_codes:
        raise RuntimeError(
            f"fixture-source CONTINUE unexpectedly had Re-KY reasons: {reason_codes!r}"
        )

    summary = {
        "dogfood": "PASS",
        "classification": "PARTIAL_RUNTIME_DOGFOOD",
        "fresh_process": True,
        "parent_pid": os.getpid(),
        "worker_pid": receipt["worker_pid"],
        "task_id": receipt["task_id"],
        "operation": receipt["operation"],
        "target": receipt["target"],
        "content_sha256": receipt["content_sha256"],
        "bytes_read": receipt["bytes_read"],
        "target_identity_unchanged": receipt["target_identity_unchanged"],
        "handoff_fingerprint": receipt["handoff_fingerprint"],
        "authority_granted": False,
        "source_bindings_observed": True,
        "source_observer_scope": "dogfood_local_fixtures_only",
        "reky_runtime_evaluated": True,
        "reky_runtime_outcome": reky.outcome,
        "reky_reason_codes": reason_codes,
        "fixture_reky_runtime_continuation_observed": True,
        "full_reky_runtime_continuation_claimed": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
