import json
from dataclasses import fields
from pathlib import Path

from nazeyatta.verification import VERIFICATION_OUTCOMES, VerificationReceipt
from nazeyatta.evaluator import (
    EVIDENCE_LANES,
    EVIDENCE_STATES,
    OUTCOME_RANK,
    Receipt,
    TASK_EXTERNALITIES,
    TASK_SIDE_EFFECTS,
)

ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_task_schema_matches_shared_runtime_contract():
    schema = _schema("task.schema.json")
    props = schema["properties"]

    assert set(schema["required"]) == {"task_id", "action", "semantics", "evidence"}
    assert props["task_id"]["type"] == "string"
    assert props["task_id"]["minLength"] == 1

    action = props["action"]
    assert set(action["required"]) == {"operation", "side_effect", "externality"}
    assert action["properties"]["operation"]["type"] == "string"
    assert action["properties"]["operation"]["minLength"] == 1
    assert set(action["properties"]["side_effect"]["enum"]) == TASK_SIDE_EFFECTS
    assert set(action["properties"]["externality"]["enum"]) == TASK_EXTERNALITIES

    semantics = props["semantics"]
    assert set(semantics["required"]) == {"critical_meaning_complete"}
    assert semantics["properties"]["critical_meaning_complete"]["type"] == "boolean"

    assert props["worker"]["type"] == "object"
    assert props["data"]["type"] == "object"
    assert props["evidence"]["type"] == "object"
    assert set(props["schema_version"]["enum"]) == {"0.1", "0.2"}

    v02_requirement = schema["allOf"][0]
    assert v02_requirement["if"]["properties"]["schema_version"]["const"] == "0.2"
    assert v02_requirement["then"]["required"] == ["evidence_records"]
    assert props["evidence_records"]["type"] == "object"


def test_evidence_schema_state_enum_matches_runtime():
    schema = _schema("evidence.schema.json")
    states = schema["properties"]["verification"]["properties"]["state"]["enum"]
    assert set(states) == EVIDENCE_STATES


def test_receipt_schema_matches_emitted_receipt_contract():
    schema = _schema("receipt.schema.json")
    props = schema["properties"]
    receipt_fields = {field.name for field in fields(Receipt)}

    assert set(schema["required"]) == receipt_fields
    assert set(props) == receipt_fields
    assert props["schema_version"]["const"] == "0.2"
    assert set(props["outcome"]["enum"]) == set(OUTCOME_RANK)
    assert set(props["evidence_lane"]["enum"]) == set(EVIDENCE_LANES)
    assert props["authority_granted"]["const"] is False


def test_verification_receipt_schema_matches_runtime_contract():
    schema = _schema("post-action-verification-receipt.schema.json")
    props = schema["properties"]
    receipt_fields = {field.name for field in fields(VerificationReceipt)}

    assert set(schema["required"]) == receipt_fields
    assert set(props) == receipt_fields
    assert props["schema_version"]["const"] == "0.1"
    assert props["classification"]["const"] == "POST_ACTION_VERIFICATION_RECEIPT"
    assert set(props["outcome"]["enum"]) == VERIFICATION_OUTCOMES
    assert props["authority_granted"]["const"] is False
    assert props["retry_authorized"]["const"] is False


def test_verification_request_and_observation_schema_preserve_frozen_states():
    request = _schema("post-action-verification-request.schema.json")
    observation = _schema("post-action-observation.schema.json")

    assert request["properties"]["classification"]["const"] == "POST_ACTION_VERIFICATION_REQUEST"
    assert request["properties"]["authority_granted"]["const"] is False
    assert request["properties"]["expected_facts"]["minProperties"] == 1
    assert request["properties"]["expected_facts"]["maxProperties"] == 64

    observed_fact = observation["properties"]["observed_facts"]["additionalProperties"]
    assert set(observed_fact["properties"]["observation_state"]["enum"]) == {
        "OBSERVED",
        "UNKNOWN",
    }
    assert observation["properties"]["authority_granted"]["const"] is False
