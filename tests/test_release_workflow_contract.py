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

    dispatch = document["on"]["workflow_dispatch"]
    release_channel = dispatch["inputs"]["release_channel"]
    assert release_channel["required"] == "true"
    assert release_channel["type"] == "choice"
    assert release_channel["default"] == "prerelease"
    assert release_channel["options"] == ["prerelease", "stable"]

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
    assert 'RELEASE_CHANNEL' in build_text
    assert 'RELEASE_CHANNEL' in publish_text
    assert '--prerelease' in publish_text
    assert 'Stable CLI Core != Production Enforcement Platform' in publish_text
    assert 'Technical Prerelease != Production Ready' in publish_text
    assert (
        "External first-time Human onboarding observation remains open under Issue #4"
        in publish_text
    )


def test_pypi_write_is_human_gated_manual_and_oidc_scoped():
    document = _load(PYPI_RELEASE)
    _only_manual_dispatch(document)
    assert document["permissions"]["contents"] == "read"
    assert document["concurrency"]["group"] == "nazeyatta-release"

    dispatch = document["on"]["workflow_dispatch"]
    release_channel = dispatch["inputs"]["release_channel"]
    assert release_channel["required"] == "true"
    assert release_channel["type"] == "choice"
    assert release_channel["default"] == "prerelease"
    assert release_channel["options"] == ["prerelease", "stable"]

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
    assert "RELEASE_CHANNEL" in text
    assert "EXPECTED_PRERELEASE" in text
    assert "release_channel=$RELEASE_CHANNEL" in text
    assert "publication_performed=true" in text

def test_pypi_release_runs_exact_artifact_closed_loop_self_dogfood():
    document = _load(PYPI_RELEASE)
    steps = document["jobs"]["publish-pypi"]["steps"]
    names = [step.get("name", "") for step in steps if isinstance(step, dict)]

    pre_name = "Run NazeYatta preflight from exact GitHub Release wheel"
    publish_name = "Publish through environment-scoped PyPI Trusted Publisher"
    post_name = "Live self-verify with exact PyPI re-downloaded wheel"
    upload_name = "Upload PyPI publication evidence"

    assert names.index(pre_name) < names.index(publish_name) < names.index(post_name) < names.index(upload_name)

    by_name = {
        step.get("name"): step
        for step in steps
        if isinstance(step, dict) and step.get("name")
    }
    preflight = by_name[pre_name]["run"]
    postflight = by_name[post_name]["run"]

    assert 'git show "$FINAL_COMMIT:tools/live_release_closed_loop.py"' in preflight
    assert '.release-preflight/bin/python -m pip install "pypi-dist/$WHEEL"' in preflight
    assert ".release-preflight/bin/nazeyatta check" in preflight
    assert "--require-lane provenance-v0.2" in preflight
    assert "live-preflight-receipt.json" in preflight
    assert "live-verification-request.json" in preflight

    assert 'git show "$FINAL_COMMIT:tools/live_release_closed_loop.py"' in postflight
    assert '.public-verify/bin/python -m pip install "pypi-redownload/$WHEEL"' in postflight
    assert ".public-verify/bin/nazeyatta verify" in postflight
    assert "live-post-action-observation.json" in postflight
    assert "live-verification-receipt.json" in postflight
    assert '"VERIFIED_SUCCESS"' in postflight
    assert ".authority_granted == false" in postflight
    assert ".retry_authorized == false" in postflight
