from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil

from nazeyatta.evaluator import load_yaml
from nazeyatta.fresh_handoff import compile_fresh_handoff
from nazeyatta.ky_gate import evaluate_ky_gate
from nazeyatta.reky_gate import build_boundary_observation, evaluate_reky_gate
from nazeyatta.runtime_fixture_sources import observe_fixture_sources

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TEMPLATE = ROOT / "tests" / "fixtures" / "source-observation"

AUTHORITY_REF = "authority://dogfood/ci-safe-read-only"
POLICY_REF = "policy://dogfood/runtime-safe-read-v0-1"
EVIDENCE_REF = "evidence://dogfood/fixture-exists"


def build_handoff():
    declaration = load_yaml(ROOT / "examples/worker-ky-safe-read-runtime.yaml")
    baseline = load_yaml(ROOT / "examples/ky-baseline-safe-read-runtime.yaml")
    gate = evaluate_ky_gate(declaration, baseline)
    assert gate.outcome == "PASS"
    return compile_fresh_handoff(
        declaration,
        baseline,
        gate,
        handoff_id="HANDOFF-FIXTURE-REKY-TEST",
    )


def observe(root: Path, handoff):
    return observe_fixture_sources(
        manifest_path=root / "manifest.json",
        source_root=root,
        authority_ref=handoff.source_refs["authority_ref"],
        policy_ref=handoff.source_refs["policy_ref"],
        evidence_refs=list(handoff.source_refs["evidence_refs"]),
    )


def boundary_observation(
    *,
    handoff,
    observation_id: str,
    observed_at: datetime,
    source_snapshot: dict,
):
    return build_boundary_observation(
        handoff,
        observation_id=observation_id,
        target_binding={
            "kind": "file",
            "identifier": handoff.intended_action["target"],
            "identity_fingerprint": "sha256:stable-target-identity",
        },
        source_snapshot=source_snapshot,
        observed_by={
            "type": "workflow",
            "identifier": "fixture-source-change-test",
        },
        observed_at=observed_at.isoformat(),
    )


def test_policy_fixture_change_between_observations_requires_reky(tmp_path):
    source_root = tmp_path / "source-observation"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    handoff = build_handoff()

    t0 = datetime(2026, 9, 22, tzinfo=timezone.utc)
    before_sources = observe(source_root, handoff)

    policy_path = source_root / "policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["fixture_revision_marker"] = "changed-after-before-observation"
    policy_path.write_text(
        json.dumps(policy, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    after_sources = observe(source_root, handoff)

    before = boundary_observation(
        handoff=handoff,
        observation_id="OBS-SOURCE-BEFORE",
        observed_at=t0,
        source_snapshot=before_sources,
    )
    after = boundary_observation(
        handoff=handoff,
        observation_id="OBS-SOURCE-AFTER",
        observed_at=t0 + timedelta(seconds=1),
        source_snapshot=after_sources,
    )

    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "RE_KY"
    assert any(
        reason["code"] == "POLICY_BINDING_CHANGED"
        for reason in result.reasons
    )


def test_unchanged_fixture_sources_allow_continue(tmp_path):
    source_root = tmp_path / "source-observation"
    shutil.copytree(SOURCE_TEMPLATE, source_root)
    handoff = build_handoff()

    t0 = datetime(2026, 9, 22, tzinfo=timezone.utc)
    before_sources = observe(source_root, handoff)
    after_sources = observe(source_root, handoff)

    before = boundary_observation(
        handoff=handoff,
        observation_id="OBS-STABLE-BEFORE",
        observed_at=t0,
        source_snapshot=before_sources,
    )
    after = boundary_observation(
        handoff=handoff,
        observation_id="OBS-STABLE-AFTER",
        observed_at=t0 + timedelta(seconds=1),
        source_snapshot=after_sources,
    )

    result = evaluate_reky_gate(handoff, before, after)
    assert result.outcome == "CONTINUE"
    assert result.reasons == []
