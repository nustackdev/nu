"""Shared fixtures: a filled mount dir, and a runner that runs a term sync or async."""

from __future__ import annotations

import asyncio

import pytest

import nu


class Runner:
    """Runs a term under ``nu.run`` or ``nu.arun``, by ``mode``, and gives its value."""

    def __init__(self, mode: str) -> None:
        self.mode = mode

    def __call__(self, term):
        if self.mode == "sync":
            return nu.run(term)[0]
        return asyncio.run(nu.arun(term))[0]


@pytest.fixture(params=["sync", "async"])
def go(request):
    """A ``Runner`` for each mode."""
    return Runner(request.param)


@pytest.fixture
def root(tmp_path):
    """A mount dir holding a few files and dirs::

    a.txt          "hello\\nworld\\n"
    bin.dat        bytes 0..255
    docs/          readme.md, notes.md, sub/deep.md
    empty/
    """
    base = tmp_path / "root"
    base.mkdir()
    (base / "a.txt").write_text("hello\nworld\n")
    (base / "bin.dat").write_bytes(bytes(range(256)))
    (base / "docs" / "sub").mkdir(parents=True)
    (base / "docs" / "readme.md").write_text("# readme\n")
    (base / "docs" / "notes.md").write_text("notes")
    (base / "docs" / "sub" / "deep.md").write_text("deep")
    (base / "empty").mkdir()
    return base
