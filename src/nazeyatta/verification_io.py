from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from .verification import VerificationReceipt


def deterministic_verification_receipt_json(receipt: VerificationReceipt) -> str:
    return (
        json.dumps(
            asdict(receipt),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def write_verification_receipt_json(
    receipt: VerificationReceipt,
    path: str | Path,
) -> Path:
    target = Path(path)
    data = deterministic_verification_receipt_json(receipt)

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
