from datetime import datetime
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_contract():
    schema = json.loads((ROOT / "schemas/worker-ky.schema.json").read_text(encoding="utf-8"))
    example = yaml.safe_load((ROOT / "examples/worker-ky-preview.yaml").read_text(encoding="utf-8"))
    return schema, example


def test_worker_ky_schema_is_closed_and_self_report_only():
    schema, _ = load_contract()
    assert schema["$id"] == "urn:nazeyatta:schema:worker-ky:0.2"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["classification"]["const"] == "WORKER_SELF_REPORT"
    assert schema["properties"]["declared_by"]["properties"]["type"]["const"] == "worker"


def test_worker_ky_scope_is_machine_readable_action_atoms():
    schema, example = load_contract()
    assert schema["properties"]["intended_action"]["$ref"] == "#/$defs/actionAtom"
    for field in ("understood_allowed_scope", "understood_forbidden_scope"):
        assert schema["properties"][field]["$ref"] == "#/$defs/actionAtoms"
        values = example[field]
        assert 1 <= len(values) <= 32
        assert all(set(v) == {"operation", "target"} for v in values)


def test_worker_ky_items_have_ids_and_human_summaries():
    schema, example = load_contract()
    for field in ("recognized_hazards", "planned_controls", "stop_conditions"):
        assert schema["properties"][field]["$ref"] == "#/$defs/kyItems"
        values = example[field]
        assert 1 <= len(values) <= 32
        assert all(set(v) == {"id", "summary"} for v in values)
        ids = [v["id"] for v in values]
        assert len(ids) == len(set(ids))


def test_worker_ky_example_matches_required_contract_shape():
    schema, example = load_contract()
    assert set(schema["required"]) <= set(example)
    assert example["classification"] == "WORKER_SELF_REPORT"
    assert example["declared_by"]["type"] == "worker"
    assert example["schema_version"] == "0.2"


def test_worker_ky_example_contains_no_verified_evidence_claim():
    _, example = load_contract()
    dumped = json.dumps(example, sort_keys=True)
    assert "VERIFIED" not in dumped
    assert "evidence" not in {k.lower() for k in example}


def test_worker_ky_example_timestamp_is_timezone_aware():
    _, example = load_contract()
    value = example["declared_at"]
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
