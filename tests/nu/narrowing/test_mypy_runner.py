"""Run mypy against the whole ``tests/nu/narrowing/`` directory.

Wraps every ``assert_type`` / ``# type: ignore`` sanity into one pytest
so ``pytest tests/nu`` catches static-narrowing regressions. Each other
file in this directory contains no runtime behavior - they exist purely
to exercise mypy's inference. Runtime pytest collects them and finds no
tests; this runner is what actually verifies them.

Skipped when mypy is not installed in the venv (so the suite stays green
on machines without a type-checker).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


NARROWING_DIR = Path(__file__).parent
MYPY_CONFIG = NARROWING_DIR / "mypy.ini"


def _mypy_available() -> bool:
    try:
        import mypy  # noqa: F401 - import-check only
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _mypy_available(), reason="mypy not installed")
def test_narrowing_suite_passes_mypy() -> None:
    """Every file in ``tests/nu/narrowing/`` must pass mypy cleanly.

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
    )
    if result.returncode != 0:
        pytest.fail(
            f"mypy narrowing suite failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
