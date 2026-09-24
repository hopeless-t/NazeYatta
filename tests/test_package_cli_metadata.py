from importlib.metadata import version
from pathlib import Path
import subprocess
import sys
import tomllib

import nazeyatta


ROOT = Path(__file__).resolve().parents[1]


def test_cli_version_matches_package_and_runtime_version():
    proc = subprocess.run(
        [sys.executable, "-m", "nazeyatta.cli", "--version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
    assert proc.stdout.strip() == f"nazeyatta {nazeyatta.__version__}"
    assert nazeyatta.__version__ == version("nazeyatta")


def test_project_metadata_has_public_navigation_urls():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    urls = data["project"]["urls"]

    assert urls == {
        "Homepage": "https://github.com/hopeless-t/NazeYatta",
        "Repository": "https://github.com/hopeless-t/NazeYatta",
        "Issues": "https://github.com/hopeless-t/NazeYatta/issues",
        "Changelog": "https://github.com/hopeless-t/NazeYatta/blob/main/CHANGELOG.md",
    }


def test_python_312_classifier_is_declared():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "Programming Language :: Python :: 3.12" in data["project"]["classifiers"]
