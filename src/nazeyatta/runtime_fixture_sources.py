from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

EVIDENCE_STATES = {"VERIFIED", "PRESENT", "STALE", "INVALID", "MISSING", "UNKNOWN"}
SOURCE_KINDS = {"authority", "policy", "evidence"}
MAX_SOURCE_BYTES = 1_048_576
MAX_MANIFEST_BYTES = 1_048_576
MAX_SOURCES = 32


class FixtureSourceObservationError(ValueError):
    """The bounded dogfood fixture observer cannot produce a truthful observation."""


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureSourceObservationError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise FixtureSourceObservationError(
            f"{where} is missing required keys: {sorted(missing)!r}"
        )
    if extra:
        raise FixtureSourceObservationError(
            f"{where} has unsupported keys: {sorted(extra)!r}"
        )


def _string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise FixtureSourceObservationError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise FixtureSourceObservationError(
            f"{where} must be at most {max_len} characters"
        )
    return value


def _read_bounded(path: Path, limit: int, where: str) -> bytes:
    if not path.is_file():
        raise FixtureSourceObservationError(f"{where} must resolve to a regular file")
    size = path.stat().st_size
    if size > limit:
        raise FixtureSourceObservationError(f"{where} exceeds {limit} bytes")
    return path.read_bytes()


def _resolve_under_root(root: Path, relative: str, where: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise FixtureSourceObservationError(f"{where} must stay beneath source root")
    try:
        resolved = (root / rel).resolve(strict=True)
    except OSError as exc:
        raise FixtureSourceObservationError(f"{where} cannot be resolved") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FixtureSourceObservationError(f"{where} escapes source root") from exc
    if not resolved.is_file():
        raise FixtureSourceObservationError(f"{where} must resolve to a regular file")
    return resolved


def _load_manifest(manifest_path: str | Path, source_root: str | Path) -> dict[str, dict[str, str]]:
    root = Path(source_root).resolve(strict=True)
    if not root.is_dir():
        raise FixtureSourceObservationError("source_root must be a directory")

    manifest = Path(manifest_path).resolve(strict=True)
    try:
        manifest.relative_to(root)
    except ValueError as exc:
        raise FixtureSourceObservationError("manifest must stay beneath source root") from exc

    raw = _read_bounded(manifest, MAX_MANIFEST_BYTES, "manifest")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureSourceObservationError("manifest must be valid UTF-8 JSON") from exc

    data = _mapping(data, "manifest")
    _exact_keys(
        data,
        {"schema_version", "classification", "sources"},
        "manifest",
    )
    if data.get("schema_version") != "0.1":
        raise FixtureSourceObservationError("manifest.schema_version must be '0.1'")
    if data.get("classification") != "DOGFOOD_FIXTURE_SOURCE_MANIFEST":
        raise FixtureSourceObservationError(
            "manifest.classification must be DOGFOOD_FIXTURE_SOURCE_MANIFEST"
        )

    sources = _mapping(data.get("sources"), "manifest.sources")
    if len(sources) > MAX_SOURCES:
        raise FixtureSourceObservationError(
            f"manifest.sources must contain at most {MAX_SOURCES} entries"
        )

    checked: dict[str, dict[str, str]] = {}
    for ref, raw_entry in sources.items():
        ref = _string(ref, "manifest source ref")
        entry = _mapping(raw_entry, f"manifest.sources[{ref!r}]")
        _exact_keys(entry, {"kind", "path"}, f"manifest.sources[{ref!r}]")
        kind = _string(entry.get("kind"), f"manifest.sources[{ref!r}].kind", max_len=32)
        if kind not in SOURCE_KINDS:
            raise FixtureSourceObservationError(
                f"manifest.sources[{ref!r}].kind is unsupported"
            )
        relative = _string(entry.get("path"), f"manifest.sources[{ref!r}].path")
        _resolve_under_root(root, relative, f"manifest.sources[{ref!r}].path")
        checked[ref] = {"kind": kind, "path": relative}
    return checked


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _observe_one(
    *,
    ref: str,
    expected_kind: str,
    manifest: dict[str, dict[str, str]],
    source_root: Path,
) -> tuple[dict[str, Any], bytes]:
    if ref not in manifest:
        raise FixtureSourceObservationError(f"source ref {ref!r} is not in manifest")
    entry = manifest[ref]
    if entry["kind"] != expected_kind:
        raise FixtureSourceObservationError(
            f"source ref {ref!r} has kind {entry['kind']!r}, expected {expected_kind!r}"
        )

    path = _resolve_under_root(source_root, entry["path"], f"source {ref!r}")
    payload = _read_bounded(path, MAX_SOURCE_BYTES, f"source {ref!r}")
    binding = {
        "ref": ref,
        "observation_state": "OBSERVED",
        "binding_token": _sha256(payload),
    }
    return binding, payload


def observe_fixture_sources(
    *,
    manifest_path: str | Path,
    source_root: str | Path,
    authority_ref: str,
    policy_ref: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    root = Path(source_root).resolve(strict=True)
    manifest = _load_manifest(manifest_path, root)

    authority, _ = _observe_one(
        ref=authority_ref,
        expected_kind="authority",
        manifest=manifest,
        source_root=root,
    )
    policy, _ = _observe_one(
        ref=policy_ref,
        expected_kind="policy",
        manifest=manifest,
        source_root=root,
    )

    evidence_bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in evidence_refs:
        ref = _string(ref, "evidence ref")
        if ref in seen:
            raise FixtureSourceObservationError(f"duplicate evidence ref {ref!r}")
        seen.add(ref)

        binding, payload = _observe_one(
            ref=ref,
            expected_kind="evidence",
            manifest=manifest,
            source_root=root,
        )
        try:
            evidence = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FixtureSourceObservationError(
                f"evidence source {ref!r} must be valid UTF-8 JSON"
            ) from exc
        evidence = _mapping(evidence, f"evidence source {ref!r}")
        state = evidence.get("state")
        if state not in EVIDENCE_STATES:
            raise FixtureSourceObservationError(
                f"evidence source {ref!r} has invalid state {state!r}"
            )
        evidence_bindings.append({**binding, "state": state})

    return {
        "authority_binding": authority,
        "policy_binding": policy,
        "evidence_bindings": evidence_bindings,
    }
