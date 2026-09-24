import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_closed_loop_release_dogfood_proves_success_and_visible_mismatch():
    proc = subprocess.run(
        [sys.executable, "tools/dogfood_closed_loop_verification.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)

    assert payload["success_case"]["outcome"] == "VERIFIED_SUCCESS"
    assert payload["intentional_mismatch_case"]["outcome"] == "VERIFIED_FAILURE"
    reasons = payload["intentional_mismatch_case"]["reasons"]
    assert reasons == [
        {
            "code": "FACT_MISMATCH",
            "expected": False,
            "fact_id": "github_release_prerelease",
            "observation_state": "OBSERVED",
            "observed": True,
        }
    ]
    assert payload["authority_granted"] is False
    assert payload["retry_authorized"] is False
