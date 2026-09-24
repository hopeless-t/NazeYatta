import json
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from nazeyatta.cli import packaged_schema_path


ROOT = Path(__file__).resolve().parents[1]

CASES = {
    "task": ("schemas/task.schema.json", "urn:nazeyatta:schema:task:0.2"),
    "evidence": ("schemas/evidence.schema.json", "urn:nazeyatta:schema:evidence:0.2"),
    "receipt": ("schemas/receipt.schema.json", "urn:nazeyatta:schema:receipt:0.2"),
}


@pytest.mark.parametrize("name, expected", CASES.items())
def test_packaged_core_schema_bytes_match_repository_source(name, expected):
    source_path, _ = expected
    assert packaged_schema_path(name).read_bytes() == (ROOT / source_path).read_bytes()


@pytest.mark.parametrize("name, expected", CASES.items())
def test_schema_command_prints_exact_valid_json(name, expected):
    source_path, schema_id = expected
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "schema", name],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
    assert proc.stdout == (ROOT / source_path).read_text(encoding="utf-8")
    assert json.loads(proc.stdout)["$id"] == schema_id


def test_schema_command_rejects_unknown_name():
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "schema", "../other"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr


def test_pyproject_declares_packaged_schema_data():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "schemas/*.json" in data["tool"]["setuptools"]["package-data"]["nazeyatta"]
