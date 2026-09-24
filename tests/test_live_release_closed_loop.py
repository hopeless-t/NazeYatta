from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

from nazeyatta.evaluator import evaluate, load_yaml, stable_hash
from tools.live_release_closed_loop import (
    build_observation,
    build_preflight_task,
    build_verification_request,
)
from nazeyatta.verification import verify_post_action


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies/generic/rules.yaml"
VERSION = "1.1.0.dev0"
FINAL_COMMIT = "e9cb9373e95a6b7ec2e767bd78412a801c7b3b47"
OBSERVED_AT = "2026-09-25T03:30:00+09:00"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_files(tmp_path: Path):
    wheel = tmp_path / f"nazeyatta-{VERSION}-py3-none-any.whl"
    sdist = tmp_path / f"nazeyatta-{VERSION}.tar.gz"
    wheel.write_bytes(b"wheel-live-self-dogfood")
    sdist.write_bytes(b"sdist-live-self-dogfood")
    sums = tmp_path / "SHA256SUMS.txt"
    sums.write_text(
        f"{_sha256(wheel)}  {wheel.name}\n{_sha256(sdist)}  {sdist.name}\n",
        encoding="utf-8",
    )
    return wheel, sdist, sums


def _task_and_receipt(tmp_path: Path):
    wheel, sdist, sums = _fixture_files(tmp_path)
    task = build_preflight_task(
        version=VERSION,
        final_commit=FINAL_COMMIT,
        release_channel="prerelease",
        repository="hopeless-t/NazeYatta",
        sha256s_path=sums,
        observed_at=OBSERVED_AT,
    )
    receipt = evaluate(task, load_yaml(POLICY))
    return wheel, sdist, task, receipt


def test_live_release_preflight_is_real_v02_pass_but_never_grants_authority(tmp_path):
    _, _, task, receipt = _task_and_receipt(tmp_path)

    assert task["schema_version"] == "0.2"
    assert task["action"]["target"]["source_release_commit"] == FINAL_COMMIT
    assert receipt.outcome == "PASS"
    assert receipt.evidence_lane == "provenance-v0.2"
    assert receipt.authority_granted is False


def test_live_release_request_binds_actual_preflight_receipt(tmp_path):
    _, _, task, receipt = _task_and_receipt(tmp_path)
    request = build_verification_request(
        task=task,
        preflight_receipt=receipt.__dict__,
    )

    assert request["preflight_receipt_fingerprint"] == stable_hash(receipt.__dict__)
    assert request["task_fingerprint"] == receipt.task_fingerprint
    assert request["action_fingerprint"] == stable_hash(task["action"])
    assert request["target_binding"]["identity_fingerprint"] == stable_hash(task["action"]["target"])
    assert request["authority_granted"] is False


def test_live_public_observation_can_succeed_and_preserves_mismatch(tmp_path):
    wheel, sdist, task, receipt = _task_and_receipt(tmp_path)
    request = build_verification_request(
        task=task,
        preflight_receipt=receipt.__dict__,
    )
    release = {
        "prerelease": True,
        "target_commitish": FINAL_COMMIT,
    }
    pypi = {"info": {"version": VERSION}}

    observation = build_observation(
        request=request,
        release_payload=release,
        pypi_payload=pypi,
        wheel_path=wheel,
        sdist_path=sdist,
        observed_at=OBSERVED_AT,
    )
    success = verify_post_action(request, observation)
    assert success.outcome == "VERIFIED_SUCCESS"
    assert success.authority_granted is False
    assert success.retry_authorized is False

    mismatched = deepcopy(observation)
    mismatched["observed_facts"]["github_release_prerelease"]["value"] = False
    failure = verify_post_action(request, mismatched)
    assert failure.outcome == "VERIFIED_FAILURE"
    assert failure.reasons[0]["fact_id"] == "github_release_prerelease"
