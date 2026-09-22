from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

from .evaluator import stable_hash

MAX_HANDOFF_BYTES = 1_048_576
TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,127}$")

HANDOFF_KEYS = {
    "schema_version",
    "handoff_id",
    "classification",
    "task_id",
    "intended_action",
    "admitted_actions",
    "forbidden_actions",
    "required_hazard_ids",
    "required_control_ids",
    "required_stop_condition_ids",
    "source_refs",
    "bindings",
    "validity",
    "authority_granted",
}


class SafeReadRuntimeError(ValueError):
    """The bounded safe-read worker cannot execute the supplied handoff safely."""


def _require_mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SafeReadRuntimeError(f"{where} must be a mapping")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise SafeReadRuntimeError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise SafeReadRuntimeError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _require_string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise SafeReadRuntimeError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise SafeReadRuntimeError(f"{where} must be at most {max_len} characters")
    return value


def _action(value: Any, where: str) -> dict[str, str]:
    item = _require_mapping(value, where)
    _require_exact_keys(item, {"operation", "target"}, where)
    operation = _require_string(item.get("operation"), f"{where}.operation", max_len=128)
    target = _require_string(item.get("target"), f"{where}.target", max_len=128)
    return {"operation": operation, "target": target}


def load_handoff(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise SafeReadRuntimeError("handoff file does not exist")
    if p.stat().st_size > MAX_HANDOFF_BYTES:
        raise SafeReadRuntimeError("handoff file is too large")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SafeReadRuntimeError(f"handoff JSON could not be read: {exc}") from exc
    handoff = _require_mapping(data, "handoff")
    _require_exact_keys(handoff, HANDOFF_KEYS, "handoff")

    if handoff.get("schema_version") != "0.1":
        raise SafeReadRuntimeError("handoff.schema_version must be '0.1'")
    if handoff.get("classification") != "KY_VALIDATED_HANDOFF":
        raise SafeReadRuntimeError(
            "handoff.classification must be KY_VALIDATED_HANDOFF"
        )
    if handoff.get("authority_granted") is not False:
        raise SafeReadRuntimeError("handoff must not grant execution authority")
    if handoff.get("validity") != {
        "mode": "single_bounce",
        "runtime_state_bound": False,
    }:
        raise SafeReadRuntimeError("unsupported handoff validity contract")

    _require_string(handoff.get("handoff_id"), "handoff.handoff_id", max_len=128)
    _require_string(handoff.get("task_id"), "handoff.task_id", max_len=128)

    intended = _action(handoff.get("intended_action"), "handoff.intended_action")
    if intended["operation"] != "read":
        raise SafeReadRuntimeError("safe-read worker accepts only operation='read'")

    admitted = handoff.get("admitted_actions")
    if not isinstance(admitted, list) or len(admitted) != 1:
        raise SafeReadRuntimeError("safe-read worker requires exactly one admitted action")
    admitted_action = _action(admitted[0], "handoff.admitted_actions[0]")
    if admitted_action != intended:
        raise SafeReadRuntimeError("admitted action must exactly match intended action")

    target = intended["target"]
    target_path = Path(target)
    if target_path.is_absolute() or ".." in target_path.parts:
        raise SafeReadRuntimeError("safe-read target must stay beneath the allowed root")
    if not TARGET_RE.fullmatch(target):
        raise SafeReadRuntimeError(
            "safe-read target must be a normalized relative path token"
        )

    # The runtime adapter structurally validates the handoff but does not authenticate
    # who produced it. Handoff authenticity remains an upstream trust boundary.
    return handoff


def _resolve_target(allowed_root: str | Path, logical_target: str) -> tuple[Path, Path]:
    root = Path(allowed_root).resolve(strict=True)
    if not root.is_dir():
        raise SafeReadRuntimeError("allowed root must be a directory")

    candidate = (root / logical_target).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SafeReadRuntimeError("resolved target escapes the allowed root") from exc

    if not candidate.is_file():
        raise SafeReadRuntimeError("resolved target must be a regular file")
    return root, candidate


def _identity_fingerprint(root: Path, target: Path, logical_target: str) -> str:
    info = target.stat()
    return stable_hash(
        {
            "logical_target": logical_target,
            "resolved_relative_path": target.relative_to(root).as_posix(),
            "device": int(getattr(info, "st_dev", 0)),
            "inode": int(getattr(info, "st_ino", 0)),
            "file_type": int(stat.S_IFMT(info.st_mode)),
        }
    )


def execute_safe_read(handoff: dict[str, Any], allowed_root: str | Path) -> dict[str, Any]:
    intended = handoff["intended_action"]
    logical_target = intended["target"]
    root, target = _resolve_target(allowed_root, logical_target)

    before_identity = _identity_fingerprint(root, target, logical_target)
    payload = target.read_bytes()
    after_identity = _identity_fingerprint(root, target, logical_target)

    content_sha256 = "sha256:" + hashlib.sha256(payload).hexdigest()
    unchanged = before_identity == after_identity

    return {
        "schema_version": "0.1",
        "classification": "RUNTIME_EXECUTION_RECEIPT",
        "task_id": handoff["task_id"],
        "handoff_fingerprint": stable_hash(handoff),
        "operation": "read",
        "target": logical_target,
        "content_sha256": content_sha256,
        "bytes_read": len(payload),
        "before_target_identity_fingerprint": before_identity,
        "after_target_identity_fingerprint": after_identity,
        "target_identity_unchanged": unchanged,
        "worker_pid": os.getpid(),
        "outcome": "READ_OK" if unchanged else "TARGET_IDENTITY_CHANGED",
        "authority_granted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="nazeyatta-safe-read-worker")
    parser.add_argument("--handoff", required=True)
    parser.add_argument("--allowed-root", required=True)
    args = parser.parse_args()

    try:
        handoff = load_handoff(args.handoff)
        receipt = execute_safe_read(handoff, args.allowed_root)
    except (OSError, SafeReadRuntimeError) as exc:
        print(
            json.dumps(
                {
                    "classification": "RUNTIME_EXECUTION_ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "authority_granted": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 3

    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["outcome"] == "READ_OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
