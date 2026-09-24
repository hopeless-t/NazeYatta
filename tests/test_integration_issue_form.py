from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / ".github/ISSUE_TEMPLATE/integration-request.yml"


def test_concrete_integration_issue_form_collects_required_runtime_atoms():
    data = yaml.safe_load(FORM.read_text(encoding="utf-8"))

    assert data["name"] == "Concrete integration request"
    fields = {
        item["id"]: item
        for item in data["body"]
        if isinstance(item, dict) and "id" in item
    }

    required_ids = {
        "version",
        "consumer",
        "runtime_operation",
        "runtime_target",
        "task_mapping",
        "evidence_source",
        "placement",
        "non_pass",
    }
    assert required_ids.issubset(fields)
    for field_id in required_ids:
        assert fields[field_id]["validations"]["required"] is True

    target_description = fields["runtime_target"]["attributes"]["description"]
    assert "same target" in target_description

    acknowledgement_options = fields["acknowledgements"]["attributes"]["options"]
    assert acknowledgement_options
    assert all(option["required"] is True for option in acknowledgement_options)


def test_issue_form_preserves_intake_authority_boundaries():
    text = FORM.read_text(encoding="utf-8")

    assert "Integration Request != Implementation Authority" in text
    assert "Concrete Mapping Submitted != Mapping Verified" in text
    assert "Consumer Exists != Production Adoption" in text
    assert "credentials" in text
    assert "private customer data" in text


def test_contributing_routes_real_consumers_to_issue_form():
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "issues/new?template=integration-request.yml" in text
    assert "Integration Request != Implementation Authority" in text
