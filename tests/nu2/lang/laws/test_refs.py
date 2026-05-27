"""Ref invariant laws.

Mirrors ``src/nu2/lang/laws/refs.py``. Currently the module is empty; the
dimension agent adds ``ref_not_root``. The placeholder test records the
intended green-path shape (a Ref inside a Command).
"""

from __future__ import annotations

from _support.law_terms import Cmd, R
from _support.laws import assert_passes


def test_refs_passes_when_ref_sits_inside_a_command() -> None:
    """A Ref used as a Command's slot 0 - the canonical Ref placement."""
    assert_passes(Cmd(R()))
