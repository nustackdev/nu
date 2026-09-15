"""Run mypy against the whole ``tests/narrowing/`` directory.

Wraps every ``assert_type`` / ``# type: ignore`` sanity into one pytest
so ``pytest tests`` catches static-narrowing regressions. Each other
file in this directory contains no runtime behavior - they exist purely
to exercise mypy's inference. Runtime pytest collects them and finds no
tests; this runner is what actually verifies them.

mypy is in the dev group, so this runs on a synced venv. The skip is a
fallback for a stripped environment, not the normal path -- if you see it
skip, the venv is incomplete.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


NARROWING_DIR = Path(__file__).parent
MYPY_CONFIG = NARROWING_DIR / "mypy.ini"
REPO = NARROWING_DIR.parent.parent
# mypy does not follow `.pth`-based editable installs, so an editable dev venv
# leaves it unable to resolve `nu` and `nustd`. With `ignore_missing_imports`
# on, that does not fail loudly -- every expression degrades to `Any` and the
# assert_type checks report failures that say nothing about narrowing. Point
# mypy at the source trees so it checks what this suite is actually about.
SRC_DIRS = [
    REPO / "packages" / "nucore" / "src",
    REPO / "packages" / "nustd" / "src",
    REPO / "packages" / "nucli" / "src",
]


def _mypy_available() -> bool:
    try:
        import mypy  # noqa: F401 - import-check only
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _mypy_available(), reason="mypy not installed")
def test_narrowing_suite_passes_mypy() -> None:
    """Every file in ``tests/narrowing/`` must pass mypy cleanly.

    ``warn_unused_ignores = True`` (see ``mypy.ini``) means the negative
    tests fail if a violation ever silently starts type-checking clean -
    forcing a review of that ignore.
    """
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(MYPY_CONFIG),
            str(NARROWING_DIR),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "MYPYPATH": os.pathsep.join(str(p) for p in SRC_DIRS)},
    )
    if result.returncode != 0:
        pytest.fail(
            f"mypy narrowing suite failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
