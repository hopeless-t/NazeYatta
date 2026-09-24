from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from nazeyatta.evaluator import stable_hash


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FINAL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_CHANNELS = {"prerelease", "stable"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _write_new_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return target


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distribution_names(version: str) -> tuple[str, str]:
    if not version or any(ch.isspace() for ch in version):
        raise ValueError("version must be a non-empty token")
    return (
        f"nazeyatta-{version}-py3-none-any.whl",
        f"nazeyatta-{version}.tar.gz",
    )


def _read_expected_hashes(path: str | Path, version: str) -> dict[str, str]:
    wheel, sdist = _distribution_names(version)
    wanted = {wheel, sdist}
    found: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if len(parts) != 2:
            continue
        digest, filename = parts
        filename = filename.lstrip("*")
        if filename in wanted:
            if not SHA256_RE.fullmatch(digest):
                raise ValueError(f"invalid SHA-256 for {filename}")
            found[filename] = digest
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"missing SHA-256 entries: {sorted(missing)!r}")
    return found


def _evidence_record(evidence_id: str, claim: str, observed_at: str, artifact_ref: str) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "supports_claim": claim,
        "observed_at": observed_at,
        "observer": {
            "type": "workflow",
            "identifier": "github-actions-release",
        },
        "artifact": {"ref": artifact_ref},
        "verification": {"state": "VERIFIED"},
    }


def build_preflight_task(
    *,
    version: str,
    final_commit: str,
    release_channel: str,
    repository: str,
    sha256s_path: str | Path,
    observed_at: str,
) -> dict[str, Any]:
    if not FINAL_COMMIT_RE.fullmatch(final_commit):
        raise ValueError("final_commit must be exactly 40 lowercase hex characters")
    if release_channel not in RELEASE_CHANNELS:
        raise ValueError(f"unsupported release_channel: {release_channel!r}")
    if "/" not in repository:
        raise ValueError("repository must be owner/name")

    wheel, sdist = _distribution_names(version)
    hashes = _read_expected_hashes(sha256s_path, version)
    tag = f"v{version}"
    target = {
        "provider": "pypi",
        "project": "nazeyatta",
        "version": version,
        "source_repository": repository,
        "source_release_tag": tag,
        "source_release_commit": final_commit,
        "release_channel": release_channel,
    }

    return {
        "schema_version": "0.2",
        "task_id": f"NAZEYATTA-RELEASE-{version}-PYPI",
        "action": {
            "operation": "publish",
            "side_effect": "external_write",
            "externality": "public",
            "target": target,
        },
        "worker": {"required_capability": "publish_pypi_trusted"},
        "data": {
            "classification": "public",
            "artifacts": [
                {"filename": wheel, "sha256": hashes[wheel]},
                {"filename": sdist, "sha256": hashes[sdist]},
            ],
        },
        "semantics": {"critical_meaning_complete": True},
        "evidence": {
            "authority_verified": "EV-AUTH",
            "execution_target_verified": "EV-TARGET",
            "worker_capability_qualified": "EV-CAP",
            "provenance_verified": "EV-PROV",
            "publication_permission_verified": "EV-PERM",
            "evidence_bundle_current": "EV-CURRENT",
        },
        "evidence_records": {
            "EV-AUTH": _evidence_record(
                "EV-AUTH",
                "authority_verified",
                observed_at,
                "github-actions:workflow_dispatch+environment/release",
            ),
            "EV-TARGET": _evidence_record(
                "EV-TARGET",
                "execution_target_verified",
                observed_at,
                f"pypi:nazeyatta=={version}:prewrite-absent",
            ),
            "EV-CAP": _evidence_record(
                "EV-CAP",
                "worker_capability_qualified",
                observed_at,
                "github-actions:oidc-trusted-publisher",
            ),
            "EV-PROV": _evidence_record(
                "EV-PROV",
                "provenance_verified",
                observed_at,
                f"github-release:{repository}:{tag}:sha256-verified",
            ),
            "EV-PERM": _evidence_record(
                "EV-PERM",
                "publication_permission_verified",
                observed_at,
                "github-actions:environment/release",
            ),
            "EV-CURRENT": _evidence_record(
                "EV-CURRENT",
                "evidence_bundle_current",
                observed_at,
                f"pypi:nazeyatta=={version}:observed-immediately-before-write",
            ),
        },
    }


def build_verification_request(
    *,
    task: dict[str, Any],
    preflight_receipt: dict[str, Any],
) -> dict[str, Any]:
    if preflight_receipt.get("outcome") != "PASS":
        raise ValueError("preflight receipt must be PASS before a live verification request is prepared")
    if preflight_receipt.get("evidence_lane") != "provenance-v0.2":
        raise ValueError("preflight receipt must use provenance-v0.2")
    if preflight_receipt.get("authority_granted") is not False:
        raise ValueError("preflight receipt must not grant authority")
    if preflight_receipt.get("task_fingerprint") != stable_hash(task):
        raise ValueError("preflight receipt task_fingerprint does not bind to the supplied task")

    target = task["action"]["target"]
    version = target["version"]
    release_channel = target["release_channel"]
    artifacts = {
        item["filename"]: item["sha256"]
        for item in task["data"]["artifacts"]
    }
    wheel, sdist = _distribution_names(version)

    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_VERIFICATION_REQUEST",
        "verification_id": f"{task['task_id']}-LIVE-VERIFY",
        "task_id": task["task_id"],
        "preflight_receipt_fingerprint": stable_hash(preflight_receipt),
        "task_fingerprint": preflight_receipt["task_fingerprint"],
        "action_fingerprint": stable_hash(task["action"]),
        "target_binding": {
            "kind": "pypi_release",
            "identifier": f"pypi:nazeyatta=={version}",
            "identity_fingerprint": stable_hash(target),
        },
        "expected_facts": {
            "github_release_exists": True,
            "github_release_prerelease": release_channel == "prerelease",
            "github_release_target_commit": target["source_release_commit"],
            "pypi_public_version": version,
            "wheel_sha256": artifacts[wheel],
            "sdist_sha256": artifacts[sdist],
        },
        "authority_granted": False,
    }


def _observed(value: Any) -> dict[str, Any]:
    if type(value) in (str, bool, int):
        return {"observation_state": "OBSERVED", "value": value}
    return {"observation_state": "UNKNOWN", "value": None}


def build_observation(
    *,
    request: dict[str, Any],
    release_payload: dict[str, Any],
    pypi_payload: dict[str, Any],
    wheel_path: str | Path,
    sdist_path: str | Path,
    observed_at: str,
) -> dict[str, Any]:
    pypi_info = pypi_payload.get("info")
    if not isinstance(pypi_info, dict):
        pypi_info = {}

    wheel = Path(wheel_path)
    sdist = Path(sdist_path)
    wheel_digest: str | None = _sha256_file(wheel) if wheel.is_file() else None
    sdist_digest: str | None = _sha256_file(sdist) if sdist.is_file() else None

    observed_facts = {
        "github_release_exists": _observed(bool(release_payload)),
        "github_release_prerelease": _observed(release_payload.get("prerelease")),
        "github_release_target_commit": _observed(release_payload.get("target_commitish")),
        "pypi_public_version": _observed(pypi_info.get("version")),
        "wheel_sha256": _observed(wheel_digest),
        "sdist_sha256": _observed(sdist_digest),
    }

    return {
        "schema_version": "0.1",
        "classification": "POST_ACTION_OBSERVATION",
        "observation_id": f"{request['verification_id']}-PUBLIC-READBACK",
        "verification_id": request["verification_id"],
        "task_id": request["task_id"],
        "preflight_receipt_fingerprint": request["preflight_receipt_fingerprint"],
        "task_fingerprint": request["task_fingerprint"],
        "action_fingerprint": request["action_fingerprint"],
        "target_binding": request["target_binding"],
        "observed_facts": observed_facts,
        "observed_by": {
            "type": "workflow",
            "identifier": "github-actions-live-release-readback",
        },
        "observed_at": observed_at,
        "authority_granted": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded NazeYatta release-specific closed-loop dogfood helper"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight-task")
    pre.add_argument("--version", required=True)
    pre.add_argument("--final-commit", required=True)
    pre.add_argument("--release-channel", required=True, choices=sorted(RELEASE_CHANNELS))
    pre.add_argument("--repository", required=True)
    pre.add_argument("--sha256s", required=True)
    pre.add_argument("--observed-at", default=None)
    pre.add_argument("--out", required=True)

    req = sub.add_parser("verification-request")
    req.add_argument("--task", required=True)
    req.add_argument("--receipt", required=True)
    req.add_argument("--out", required=True)

    obs = sub.add_parser("observation")
    obs.add_argument("--request", required=True)
    obs.add_argument("--release-json", required=True)
    obs.add_argument("--pypi-json", required=True)
    obs.add_argument("--wheel", required=True)
    obs.add_argument("--sdist", required=True)
    obs.add_argument("--observed-at", default=None)
    obs.add_argument("--out", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "preflight-task":
        payload = build_preflight_task(
            version=args.version,
            final_commit=args.final_commit,
            release_channel=args.release_channel,
            repository=args.repository,
            sha256s_path=args.sha256s,
            observed_at=args.observed_at or _utc_now(),
        )
    elif args.command == "verification-request":
        payload = build_verification_request(
            task=_read_json(args.task),
            preflight_receipt=_read_json(args.receipt),
        )
    else:
        payload = build_observation(
            request=_read_json(args.request),
            release_payload=_read_json(args.release_json),
            pypi_payload=_read_json(args.pypi_json),
            wheel_path=args.wheel,
            sdist_path=args.sdist,
            observed_at=args.observed_at or _utc_now(),
        )
    _write_new_json(args.out, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
