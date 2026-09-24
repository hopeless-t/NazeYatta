from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .evaluator import Receipt


def receipt_payload(receipt: Receipt) -> dict[str, Any]:
    """Return the public Receipt payload without adding transport metadata."""
    return asdict(receipt)


def deterministic_receipt_json(receipt: Receipt) -> str:
    """Serialize a Receipt deterministically as UTF-8 JSON text.

    This is a project-local deterministic representation, not a claim of RFC 8785/JCS
    compatibility or cryptographic authentication.
    """
    return (
        json.dumps(
            receipt_payload(receipt),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def write_receipt_json(receipt: Receipt, path: str | Path) -> Path:
    """Create one deterministic receipt JSON file without overwriting existing evidence."""
    target = Path(path)
    data = deterministic_receipt_json(receipt)

    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
    except Exception:
        try:
            target.unlink()
        except OSError:
            pass
        raise

    return target
