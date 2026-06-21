"""Effects laws.

Mirrors ``src/nu2/lang/laws/effects.py``. Exercises ``ref_slots`` and
``effects_originate_at_refs``.
"""

from __future__ import annotations

from _support.law_terms import R2, Act, Cmd, FlowS, Q, R
from _support.laws import assert_fails, assert_passes, violations

from nu2.engine import Severity, gate
from nu2.lang import compile as nu_compile
from nu2.lang.attributes import Attr, Effect
from nu2.lang.laws import LAWS


# --- ref_slots ----------------------------------------------------------


def test_ref_slots_passes_when_write_slot_holds_a_ref() -> None:
    """``Cmd`` annotates slot 0 as WRITE; slot 0 is a Ref. Law holds."""
    assert_passes(Cmd(R()))


def test_ref_slots_out_of_scope_for_action_with_ref() -> None:
    """``Act`` yields, so it is out of the VOID-only ref_slots scope. Law holds."""
    assert_passes(Act(R("y")))


def test_ref_slots_fails_when_write_slot_holds_a_non_ref() -> None:
    """Slot 0 carries a Query instead of a Ref; the Command WRITE has no referent."""
    assert_fails(Cmd(Q()), "ref_slots")


def test_ref_slots_relaxes_for_addressless_action() -> None:
    """An Action's mutation slot may hold a non-Ref: addressless, it degrades to
    a Query rather than failing. The VOID-scoped law never fires on it."""
    fired = [v for v in violations(Act(Q())) if v.law == "ref_slots"]
    assert not fired


# --- effects_originate_at_refs ------------------------------------------


def test_effects_originate_at_refs_passes_for_command_subtree() -> None:
    """``Cmd(R())`` emits ``(R, WRITE)``; the subtree holds a Ref of class R."""
    assert_passes(Cmd(R()))


def test_effects_originate_at_refs_passes_for_nested_flow() -> None:
    """A Strategy with two Commands sees both Ref classes in its subtree."""
    assert_passes(FlowS(Cmd(R()), Cmd(R2())))


def test_effects_originate_at_refs_passes_for_action_in_query() -> None:
    """A Query whose subtree carries an Action still resolves its Ref class."""
    assert_passes(Q(Act(R())))


def test_effects_originate_at_refs_fails_when_column_carries_orphan_tuple() -> None:
    """Corrupt the synthesized column with a name no Ref in the subtree carries.

    The law is a sanity check on the propagation machinery: it only fires
    when the column is inconsistent with the tree below, which cannot
    arise from a well-formed compile. We inject the inconsistency directly.
    """
    program = nu_compile(Cmd(R()))
    column = program.attrs[Attr.COMPOSITION_EFFECTS]
    root_id = program.id_of[program.root]
    column[root_id] = frozenset({*column[root_id], (R2, Effect.WRITE)})
    fired = [v for v in gate(program, *LAWS) if v.law == "effects_originate_at_refs"]
    assert fired, f"expected 'effects_originate_at_refs' to fire; got: {gate(program, *LAWS)}"


def test_effects_originate_at_refs_message_names_the_orphan() -> None:
    """The violation's detail names the orphan ref class."""
    program = nu_compile(Cmd(R()))
    column = program.attrs[Attr.COMPOSITION_EFFECTS]
    root_id = program.id_of[program.root]
    column[root_id] = frozenset({*column[root_id], (R2, Effect.READ)})
    fired = [v for v in gate(program, *LAWS) if v.law == "effects_originate_at_refs"]
    assert fired and "R2" in fired[0].detail


def test_effects_originate_at_refs_fires_at_error_severity() -> None:
    """The law rejects programs at ERROR severity."""
    program = nu_compile(Cmd(R()))
    column = program.attrs[Attr.COMPOSITION_EFFECTS]
    root_id = program.id_of[program.root]
    column[root_id] = frozenset({*column[root_id], (R2, Effect.WRITE)})
    fired = [v for v in gate(program, *LAWS) if v.law == "effects_originate_at_refs"]
    assert fired[0].severity is Severity.ERROR


def test_effects_originate_at_refs_unscoped_when_composition_effects_empty() -> None:
    """A pure Query subtree has no composition_effects; the law does not fire."""
    fired = [v for v in violations(Q()) if v.law == "effects_originate_at_refs"]
    assert not fired
