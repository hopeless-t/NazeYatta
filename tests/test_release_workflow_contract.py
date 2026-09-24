from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GH_RELEASE = ROOT / ".github/workflows/publish-github-release.yml"
PYPI_RELEASE = ROOT / ".github/workflows/publish-pypi-0.2.0a1.yml"


def _load(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _only_manual_dispatch(document: dict) -> None:
    triggers = document["on"]
    assert set(triggers) == {"workflow_dispatch"}


def test_github_release_write_is_human_gated_and_manual_only():
    document = _load(GH_RELEASE)
    _only_manual_dispatch(document)
    assert document["permissions"]["contents"] == "read"
    assert document["concurrency"]["group"] == "nazeyatta-release"

    build = document["jobs"]["build-verify"]
    publish = document["jobs"]["publish-github"]
    assert "environment" not in build
    assert publish["environment"] == "release"
    assert publish["permissions"]["contents"] == "write"

    build_text = "\n".join(
        step.get("run", "") for step in build["steps"] if isinstance(step, dict)
    )
    publish_text = "\n".join(
        step.get("run", "") for step in publish["steps"] if isinstance(step, dict)
    )
    assert "gh release create" not in build_text
    assert "gh release create" in publish_text
    assert "target_observed_at=" in publish_text
    assert "write_started_at=" in publish_text
    assert (
        "External first-time Human onboarding acceptance remains PENDING under Issue #4."
        in publish_text
    )


def test_pypi_write_is_human_gated_manual_and_oidc_scoped():
    document = _load(PYPI_RELEASE)
    _only_manual_dispatch(document)
    assert document["permissions"]["contents"] == "read"
    assert document["concurrency"]["group"] == "nazeyatta-release"

    publish = document["jobs"]["publish-pypi"]
    assert publish["environment"] == "release"
    assert publish["permissions"]["contents"] == "read"
    assert publish["permissions"]["id-token"] == "write"

    uses = [
        step.get("uses", "") for step in publish["steps"] if isinstance(step, dict)
    ]
    assert "pypa/gh-action-pypi-publish@release/v1" in uses

    text = "\n".join(
        step.get("run", "") for step in publish["steps"] if isinstance(step, dict)
    )
    assert "pypi_target_state_before=absent" in text
    assert "target_observed_at=" in text
    assert "publication_performed=true" in text