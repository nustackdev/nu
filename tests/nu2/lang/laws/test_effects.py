"""Effects laws.

Mirrors ``src/nu2/lang/laws/effects.py``. Exercises ``ref_slots`` and any
laws the dimension agent adds (``effects_originate_at_refs``).
"""

from __future__ import annotations

from _support.law_terms import Cmd, Q, R
from _support.laws import assert_fails, assert_passes


def test_ref_slots_passes_when_write_slot_holds_a_ref() -> None:
    """``Cmd`` annotates slot 0 as WRITE; slot 0 is a Ref. Law holds."""
    assert_passes(Cmd(R()))


def test_ref_slots_fails_when_write_slot_holds_a_non_ref() -> None:
    """Slot 0 carries a Query instead of a Ref - the WRITE has no referent."""
    assert_fails(Cmd(Q()), "ref_slots")
