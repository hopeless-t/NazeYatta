from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json

from nazeyatta.evaluator import stable_hash
from nazeyatta.verification import verify_post_action


FINAL_COMMIT = "35799cadaa15c8b7e082dedde12e6b815397dc47"
WHEEL_SHA256 = "78335040a9806e10853682e56edd56d72d0952de236238dd190977ab2c8984b3"


def _fp(label: str) -> str:
    return stable_hash({"nazeyatta_release_dogfood": label})


def build_release_request() -> dict:
    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_VERIFICATION_REQUEST",
        "verification_id": "NAZEYATTA-V1-0-0-RELEASE-VERIFY",
        "task_id": "NAZEYATTA-V1-0-0-RELEASE",
        "preflight_receipt_fingerprint": _fp("preflight-receipt"),
        "task_fingerprint": _fp("release-task"),
        "action_fingerprint": _fp("publish-v1.0.0"),
        "target_binding": {
            "kind": "github-release",
            "identifier": "hopeless-t/NazeYatta:v1.0.0",
            "identity_fingerprint": _fp("github-release-v1.0.0"),
        },
        "expected_facts": {
            "github_release_exists": True,
            "github_release_prerelease": False,
            "github_release_target_commit": FINAL_COMMIT,
            "pypi_public_version": "1.0.0",
            "wheel_sha256": WHEEL_SHA256,
        },
        "authority_granted": False,
    }


def build_release_observation(request: dict) -> dict:
    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_OBSERVATION",
        "observation_id": "NAZEYATTA-V1-0-0-PUBLIC-READBACK",
        "verification_id": request["verification_id"],
        "task_id": request["task_id"],
        "preflight_receipt_fingerprint": request["preflight_receipt_fingerprint"],
        "task_fingerprint": request["task_fingerprint"],
        "action_fingerprint": request["action_fingerprint"],
        "target_binding": deepcopy(request["target_binding"]),
        "observed_facts": {
            key: {"observation_state": "OBSERVED", "value": value}
            for key, value in request["expected_facts"].items()
        },
        "observed_by": {
            "type": "workflow",
            "identifier": "captured-v1.0.0-publication-evidence",
        },
        "observed_at": "2026-09-25T02:25:19+09:00",
        "authority_granted": False,
    }


def main() -> int:
    request = build_release_request()
    observation = build_release_observation(request)

    success = verify_post_action(request, observation)
    if success.outcome != "VERIFIED_SUCCESS":
        raise SystemExit("expected exact captured release facts to verify successfully")

    mismatch_observation = deepcopy(observation)
    mismatch_observation["observation_id"] = "NAZEYATTA-V1-0-0-INTENTIONAL-MISMATCH"
    mismatch_observation["observed_facts"]["github_release_prerelease"]["value"] = True

    mismatch = verify_post_action(request, mismatch_observation)
    if mismatch.outcome != "VERIFIED_FAILURE":
        raise SystemExit("expected intentional release-state mismatch to fail verification")

    print(
        json.dumps(
            {
                "classification": "CLOSED_LOOP_VERIFICATION_DOGFOOD",
                "source": "captured NazeYatta v1.0.0 publication evidence",
                "success_case": asdict(success),
                "intentional_mismatch_case": asdict(mismatch),
                "authority_granted": False,
                "retry_authorized": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
