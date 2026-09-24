from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest

from nazeyatta.evaluator import stable_hash
from nazeyatta.verification import (
    VerificationError,
    verify_post_action,
)
from nazeyatta.verification_io import (
    deterministic_verification_receipt_json,
    write_verification_receipt_json,
)


def _fp(label: str) -> str:
    return stable_hash({"label": label})


def _request() -> dict:
    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_VERIFICATION_REQUEST",
        "verification_id": "VER-001",
        "task_id": "TASK-001",
        "preflight_receipt_fingerprint": _fp("preflight"),
        "task_fingerprint": _fp("task"),
        "action_fingerprint": _fp("action"),
        "target_binding": {
            "kind": "deployment",
            "identifier": "preview",
            "identity_fingerprint": _fp("target"),
        },
        "expected_facts": {
            "production_touched": False,
            "preview_updated": True,
        },
        "authority_granted": False,
    }


def _observation() -> dict:
    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_OBSERVATION",
        "observation_id": "OBS-001",
        "verification_id": "VER-001",
        "task_id": "TASK-001",
        "preflight_receipt_fingerprint": _fp("preflight"),
        "task_fingerprint": _fp("task"),
        "action_fingerprint": _fp("action"),
        "target_binding": {
            "kind": "deployment",
            "identifier": "preview",
            "identity_fingerprint": _fp("target"),
        },
        "observed_facts": {
            "production_touched": {
                "observation_state": "OBSERVED",
                "value": False,
            },
            "preview_updated": {
                "observation_state": "OBSERVED",
                "value": True,
            },
        },
        "observed_by": {
            "type": "workflow",
            "identifier": "test-observer",
        },
        "observed_at": "2026-09-25T00:00:00+09:00",
        "authority_granted": False,
    }


def test_v01_exact_success():
    receipt = verify_post_action(_request(), _observation())
    assert receipt.outcome == "VERIFIED_SUCCESS"
    assert receipt.reasons == []


def test_v02_observed_value_mismatch():
    observation = _observation()
    observation["observed_facts"]["production_touched"]["value"] = True

    receipt = verify_post_action(_request(), observation)

    assert receipt.outcome == "VERIFIED_FAILURE"
    assert receipt.reasons == [
        {
            "code": "FACT_MISMATCH",
            "fact_id": "production_touched",
            "expected": False,
            "observation_state": "OBSERVED",
            "observed": True,
        }
    ]


def test_v03_required_fact_unknown():
    observation = _observation()
    observation["observed_facts"]["production_touched"] = {
        "observation_state": "UNKNOWN",
        "value": None,
    }

    receipt = verify_post_action(_request(), observation)

    assert receipt.outcome == "UNKNOWN"
    assert receipt.reasons[0]["code"] == "FACT_UNKNOWN"


def test_v04_missing_required_observed_fact():
    observation = _observation()
    del observation["observed_facts"]["production_touched"]

    receipt = verify_post_action(_request(), observation)

    assert receipt.outcome == "UNKNOWN"
    assert receipt.reasons[0]["code"] == "FACT_NOT_OBSERVED"


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("verification_id", "VER-OTHER"),
        ("task_id", "TASK-OTHER"),
        ("preflight_receipt_fingerprint", _fp("other-preflight")),
        ("task_fingerprint", _fp("other-task")),
        ("action_fingerprint", _fp("other-action")),
    ],
)
def test_v05_to_v09_identity_binding_mismatch_rejected(field, replacement):
    observation = _observation()
    observation[field] = replacement

    with pytest.raises(VerificationError, match="does not bind"):
        verify_post_action(_request(), observation)


def test_v10_target_binding_mismatch_rejected():
    observation = _observation()
    observation["target_binding"]["identifier"] = "production"

    with pytest.raises(VerificationError, match="target_binding"):
        verify_post_action(_request(), observation)


def test_v11_malformed_observation_state_rejected():
    observation = _observation()
    observation["observed_facts"]["production_touched"]["observation_state"] = "MAYBE"

    with pytest.raises(VerificationError, match="OBSERVED or UNKNOWN"):
        verify_post_action(_request(), observation)


def test_v12_unknown_with_non_null_value_rejected():
    observation = _observation()
    observation["observed_facts"]["production_touched"] = {
        "observation_state": "UNKNOWN",
        "value": False,
    }

    with pytest.raises(VerificationError, match="must be null"):
        verify_post_action(_request(), observation)


def test_v13_observed_with_unsupported_scalar_type_rejected():
    observation = _observation()
    observation["observed_facts"]["production_touched"]["value"] = ["nope"]

    with pytest.raises(VerificationError, match="string, boolean, or integer"):
        verify_post_action(_request(), observation)


def test_v14_malformed_fact_identity_rejected():
    request = _request()
    request["expected_facts"]["Production Touched"] = request["expected_facts"].pop(
        "production_touched"
    )

    with pytest.raises(VerificationError, match="must match"):
        verify_post_action(request, _observation())


def test_type_exact_fact_comparison_does_not_treat_true_as_one():
    request = _request()
    request["expected_facts"] = {"preview_updated": True}
    observation = _observation()
    observation["observed_facts"] = {
        "preview_updated": {"observation_state": "OBSERVED", "value": 1}
    }

    receipt = verify_post_action(request, observation)

    assert receipt.outcome == "VERIFIED_FAILURE"
    assert receipt.reasons[0]["code"] == "FACT_MISMATCH"


def test_v15_request_mutation_changes_request_fingerprint():
    request = _request()
    first = verify_post_action(request, _observation())

    mutated = deepcopy(request)
    mutated["expected_facts"]["preview_updated"] = False
    observation = _observation()
    observation["observed_facts"]["preview_updated"]["value"] = False
    second = verify_post_action(mutated, observation)

    assert first.request_fingerprint != second.request_fingerprint


def test_v16_observation_mutation_changes_observation_fingerprint():
    observation = _observation()
    first = verify_post_action(_request(), observation)

    mutated = deepcopy(observation)
    mutated["observation_id"] = "OBS-002"
    second = verify_post_action(_request(), mutated)

    assert first.observation_fingerprint != second.observation_fingerprint


def test_v17_observed_contradiction_outranks_other_unknown():
    observation = _observation()
    observation["observed_facts"]["production_touched"]["value"] = True
    observation["observed_facts"]["preview_updated"] = {
        "observation_state": "UNKNOWN",
        "value": None,
    }

    receipt = verify_post_action(_request(), observation)

    assert receipt.outcome == "VERIFIED_FAILURE"
    assert {reason["code"] for reason in receipt.reasons} == {
        "FACT_MISMATCH",
        "FACT_UNKNOWN",
    }


def test_v18_receipt_never_grants_authority():
    receipt = verify_post_action(_request(), _observation())
    assert receipt.authority_granted is False


def test_v19_receipt_never_authorizes_retry():
    receipt = verify_post_action(_request(), _observation())
    assert receipt.retry_authorized is False


def test_v20_verification_receipt_output_is_deterministic_and_no_clobber(tmp_path: Path):
    receipt = verify_post_action(_request(), _observation())
    target = tmp_path / "verification.json"

    first_json = deterministic_verification_receipt_json(receipt)
    assert first_json == deterministic_verification_receipt_json(receipt)
    assert first_json.endswith("\n")

    write_verification_receipt_json(receipt, target)
    original = target.read_bytes()

    with pytest.raises(FileExistsError):
        write_verification_receipt_json(receipt, target)

    assert target.read_bytes() == original
    assert asdict(receipt)["authority_granted"] is False


def test_release_style_dogfood_success_and_intentional_mismatch():
    request = _request()
    request.update(
        {
            "verification_id": "RELEASE-V1-0-0",
            "task_id": "NAZEYATTA-RELEASE-V1-0-0",
            "target_binding": {
                "kind": "github-release",
                "identifier": "hopeless-t/NazeYatta:v1.0.0",
                "identity_fingerprint": _fp("github-release-v1.0.0"),
            },
            "expected_facts": {
                "github_release_exists": True,
                "github_release_prerelease": False,
                "github_release_target_commit": "35799cadaa15c8b7e082dedde12e6b815397dc47",
                "pypi_public_version": "1.0.0",
                "wheel_sha256": "78335040a9806e10853682e56edd56d72d0952de236238dd190977ab2c8984b3",
            },
        }
    )

    observation = _observation()
    observation.update(
        {
            "verification_id": request["verification_id"],
            "task_id": request["task_id"],
            "target_binding": deepcopy(request["target_binding"]),
            "observed_facts": {
                key: {"observation_state": "OBSERVED", "value": value}
                for key, value in request["expected_facts"].items()
            },
        }
    )

    success = verify_post_action(request, observation)
    assert success.outcome == "VERIFIED_SUCCESS"

    oops = deepcopy(observation)
    oops["observed_facts"]["github_release_prerelease"]["value"] = True
    failure = verify_post_action(request, oops)

    assert failure.outcome == "VERIFIED_FAILURE"
    assert failure.reasons[0]["fact_id"] == "github_release_prerelease"
