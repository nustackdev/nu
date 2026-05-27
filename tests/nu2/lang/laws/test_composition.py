"""Sort and composition laws.

Mirrors ``src/nu2/lang/laws/composition.py``. Exercises ``composition``,
``query_no_own_write``, ``command_has_write``, ``action_has_write``, and
``flow_body_is_mutator``.
"""

from __future__ import annotations

from _support.law_terms import Act, Brk, Cmd, FlowS, Pol, Q, R, Red, Stream
from _support.laws import assert_fails, assert_passes

from nu2.engine.structure import Declared
from nu2.lang import Command, Control, ScalarAction, ScalarQuery, Strategy
from nu2.lang.attributes import Effect


# --- malformed shapes for negative cases -------------------------------


class QWrite(ScalarQuery):
    """A ScalarQuery that wrongly declares a WRITE slot."""

    own_effects = Declared(value={0: Effect.WRITE})


class CmdNoWrite(Command):
    """A Command that wrongly declares no WRITE slot."""


class ActNoWrite(ScalarAction):
    """A ScalarAction that wrongly declares no WRITE slot."""


class FlowCQ(Control):
    """A Control with no param slots: every direct child is a body slot."""


class FlowCParam(Control):
    """A Control whose slot 0 is a yielding param; slot 1+ is body."""

    param_slots = Declared(value=frozenset({0}))


class FlowSDirect(Strategy):
    """A Strategy used for direct-child testing."""


# --- composition --------------------------------------------------------


def test_composition_passes_when_strategy_holds_command() -> None:
    """A Strategy holding a Command fits the matrix row for ``_WORK``."""
    assert_passes(FlowS(Cmd(R())))


def test_composition_fails_when_query_holds_command() -> None:
    """A Query's matrix row is ``_VALUE``; a Command yields nothing."""
    assert_fails(Q(Cmd(R())), "composition")


def test_composition_passes_when_query_holds_action() -> None:
    """An Action joins ``_VALUE``: it yields, so a Query slot accepts it."""
    assert_passes(Q(Act(R())))


def test_composition_passes_through_span() -> None:
    """A Span is transparent: a Bracket-wrapped Command fits a Strategy."""
    assert_passes(FlowS(Brk(Cmd(R()))))


# --- query_no_own_write ------------------------------------------------


def test_query_no_own_write_passes_when_query_declares_nothing() -> None:
    """A plain Query annotates no effect on itself."""
    assert_passes(Q(R()))


def test_query_no_own_write_passes_when_action_descendant_writes() -> None:
    """A Query subtree may carry WRITE through an Action descendant."""
    assert_passes(Q(Act(R())))


def test_query_no_own_write_fails_when_query_annotates_write() -> None:
    """A Query atom that annotates WRITE on itself breaks the kind contract."""
    assert_fails(QWrite(R()), "query_no_own_write")


# --- command_has_write -------------------------------------------------


def test_command_has_write_passes_for_plain_command() -> None:
    """The canonical Command shape declares WRITE on slot 0."""
    assert_passes(Cmd(R()))


def test_command_has_write_fails_when_command_declares_no_write() -> None:
    """A Command with empty ``own_effects`` is structurally a Query."""
    assert_fails(CmdNoWrite(R()), "command_has_write")


# --- action_has_write --------------------------------------------------


def test_action_has_write_passes_for_plain_action() -> None:
    """The canonical Action shape declares WRITE on slot 0."""
    assert_passes(Q(Act(R())))


def test_action_has_write_fails_when_action_declares_no_write() -> None:
    """An Action with no WRITE is a Query wearing the wrong kind."""
    assert_fails(Q(ActNoWrite(R())), "action_has_write")


# --- flow_body_is_mutator ----------------------------------------------


def test_flow_body_is_mutator_passes_when_strategy_body_is_command() -> None:
    """A Strategy holding a Command satisfies the body-mutator rule."""
    assert_passes(FlowS(Cmd(R())))


def test_flow_body_is_mutator_passes_when_strategy_body_is_action() -> None:
    """A Strategy holding an Action satisfies the body-mutator rule."""
    assert_passes(FlowS(Act(R())))


def test_flow_body_is_mutator_passes_when_strategy_body_is_flow() -> None:
    """A Flow nested in a Flow body is itself a mutator."""
    assert_passes(FlowS(FlowS(Cmd(R()))))


def test_flow_body_is_mutator_passes_through_span_body() -> None:
    """A Span wrapping a Command counts as a mutator body."""
    assert_passes(FlowS(Pol(Cmd(R()))))


def test_flow_body_is_mutator_fails_when_control_body_is_query() -> None:
    """A Flow body slot holding a Query yields a value with no consumer."""
    assert_fails(FlowCQ(Q(R())), "flow_body_is_mutator")


def test_flow_body_is_mutator_fails_when_flow_body_is_stream_through_span() -> None:
    """Span transparency does not save a non-mutator body."""
    assert_fails(FlowCQ(Brk(Stream(R()))), "flow_body_is_mutator")


def test_flow_body_is_mutator_fails_when_flow_body_is_reduction() -> None:
    """A Reduction yields a scalar; a Flow body discards it."""
    assert_fails(FlowCQ(Red(Stream(R()))), "flow_body_is_mutator")


def test_flow_body_is_mutator_skips_param_slot() -> None:
    """A Control's declared param slot accepts a yielder without firing the law."""
    assert_passes(FlowCParam(Q(R()), Cmd(R())))


def test_flow_body_is_mutator_fails_on_body_after_valid_param() -> None:
    """A Control with a valid yielding param still trips the law on a non-mutating body."""
    assert_fails(FlowCParam(Q(R()), Q(R())), "flow_body_is_mutator")


# --- control_param_is_yielder ---------------------------------------------


def test_control_param_is_yielder_passes_when_param_is_query() -> None:
    """A Control's param slot accepts a yielding Query."""
    assert_passes(FlowCParam(Q(R()), Cmd(R())))


def test_control_param_is_yielder_passes_when_param_is_action() -> None:
    """An Action is a dual-citizen: it yields, so it suits a param slot."""
    assert_passes(FlowCParam(Act(R()), Cmd(R())))


def test_control_param_is_yielder_passes_through_span_wrapping_a_yielder() -> None:
    """Span transparency carries the wrapped yielder into the param check."""
    assert_passes(FlowCParam(Brk(Q(R())), Cmd(R())))


def test_control_param_is_yielder_fails_when_param_is_command() -> None:
    """A Command yields nothing; placing it in a param slot breaks the contract."""
    assert_fails(FlowCParam(Cmd(R()), Cmd(R())), "control_param_is_yielder")


def test_control_param_is_yielder_fails_when_param_is_strategy() -> None:
    """A Strategy is mutating-only; param slots need a yielder."""
    assert_fails(FlowCParam(FlowS(Cmd(R())), Cmd(R())), "control_param_is_yielder")


def test_control_param_is_yielder_unscoped_when_no_param_slots_declared() -> None:
    """A Flow with no declared param slots has no param children to check."""
    assert_passes(FlowS(Cmd(R())))
