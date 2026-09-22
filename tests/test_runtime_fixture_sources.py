from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from nazeyatta.runtime_fixture_sources import (
    FixtureSourceObservationError,
    observe_fixture_sources,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "tests" / "fixtures" / "source-observation"
MANIFEST = SOURCE_ROOT / "manifest.json"

AUTHORITY_REF = "authority://dogfood/ci-safe-read-only"
POLICY_REF = "policy://dogfood/runtime-safe-read-v0-1"
EVIDENCE_REF = "evidence://dogfood/fixture-exists"


def observe(source_root: Path = SOURCE_ROOT, manifest: Path | None = None):
    return observe_fixture_sources(
        manifest_path=manifest or (source_root / "manifest.json"),
        source_root=source_root,
        authority_ref=AUTHORITY_REF,
        policy_ref=POLICY_REF,
        evidence_refs=[EVIDENCE_REF],
    )


def test_fixture_sources_are_actually_observed_from_bytes():
    result = observe()

    authority_bytes = (SOURCE_ROOT / "authority.json").read_bytes()
    expected_authority = "sha256:" + hashlib.sha256(authority_bytes).hexdigest()

    assert result["authority_binding"] == {
        "ref": AUTHORITY_REF,
        "observation_state": "OBSERVED",
        "binding_token": expected_authority,
    }
    assert result["policy_binding"]["observation_state"] == "OBSERVED"
    assert result["policy_binding"]["binding_token"].startswith("sha256:")

    evidence = result["evidence_bindings"][0]
    assert evidence["ref"] == EVIDENCE_REF
    assert evidence["observation_state"] == "OBSERVED"
    assert evidence["state"] == "VERIFIED"
    assert evidence["binding_token"].startswith("sha256:")


def test_unknown_source_ref_is_rejected():
    with pytest.raises(FixtureSourceObservationError, match="not in manifest"):
        observe_fixture_sources(
            manifest_path=MANIFEST,
            source_root=SOURCE_ROOT,
            authority_ref="authority://dogfood/unknown",
            policy_ref=POLICY_REF,
            evidence_refs=[EVIDENCE_REF],
        )


def test_manifest_parent_escape_is_rejected(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_ROOT, source_root)
    outside = tmp_path / "outside.json"
    outside.write_text('{"outside": true}\n', encoding="utf-8")

    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    manifest["sources"][AUTHORITY_REF]["path"] = "../outside.json"
    (source_root / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(FixtureSourceObservationError, match="stay beneath source root"):
        observe(source_root)


def test_manifest_symlink_escape_is_rejected(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_ROOT, source_root)
    outside = tmp_path / "outside.json"
    outside.write_text('{"outside": true}\n', encoding="utf-8")
    link = source_root / "escape.json"
    link.symlink_to(outside)

    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    manifest["sources"][AUTHORITY_REF]["path"] = "escape.json"
    (source_root / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(FixtureSourceObservationError, match="escapes source root"):
        observe(source_root)


def test_evidence_state_is_read_from_fixture_and_invalid_state_is_rejected(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_ROOT, source_root)

    evidence = json.loads((source_root / "evidence.json").read_text(encoding="utf-8"))
    evidence["state"] = "TRUST_ME"
    (source_root / "evidence.json").write_text(
        json.dumps(evidence), encoding="utf-8"
    )

    with pytest.raises(FixtureSourceObservationError, match="invalid state"):
        observe(source_root)


def test_manifest_source_kind_mismatch_is_rejected(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(SOURCE_ROOT, source_root)

    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    manifest["sources"][AUTHORITY_REF]["kind"] = "policy"
    (source_root / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(FixtureSourceObservationError, match="expected 'authority'"):
        observe(source_root)
