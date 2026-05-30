"""Execution-mode laws.

Mirrors ``src/nu2/lang/laws/execution.py``. Exercises
``async_atom_needs_loop`` and ``sync_atom_on_loop``. Sync vs async
behaviour is driven by ``requires_async`` and ``async_affinity``
declarations; tests use dimension-local shapes that flip those flags.
"""

from __future__ import annotations

from _support.law_terms import Cmd, FlowS, Q, R
from _support.laws import assert_fails, assert_passes, violations

from nu2.engine import Severity
from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarQuery


# --- malformed shapes for negative cases -------------------------------


class AsyncOnly(ScalarQuery):
    """A ScalarQuery that only runs async: requires the loop."""

    requires_async = Declared(value=True)


class AsyncCmd(Command):
    """A Command that only runs async. Slot 0 writes."""

    requires_async = Declared(value=True)
    mutates = Declared(value=frozenset({0}))


class SyncOnly(ScalarQuery):
    """A ScalarQuery with no async affinity: must stay off the loop."""

    async_affinity = Declared(value=False)


class SyncCmd(Command):
    """A Command with no async affinity. Slot 0 writes."""

    async_affinity = Declared(value=False)
    mutates = Declared(value=frozenset({0}))


# --- async_atom_needs_loop ---------------------------------------------


def test_async_atom_needs_loop_passes_when_async_atom_is_on_loop() -> None:
    """An async-only atom drives the root onto the loop; on_loop is True at it."""
    assert_passes(AsyncOnly())


def test_async_atom_needs_loop_passes_when_async_atom_nested_in_strategy() -> None:
    """A sequential Flow holding an async-only descendant carries on_loop down."""
    assert_passes(FlowS(Cmd(R()), AsyncCmd(R())))


# Note: with the current execution attribute machinery there is no way
# to construct a node where ``requires_async`` is True and ``on_loop``
# is False. The root pulls on_loop=True from any async-only atom in the
# subtree (sequential parents inherit it unchanged); a parallel Flow's
# derive rule sends async-only children onto the loop per child. The
# law is the catch for an attribute-computation regression rather than
# a user-reachable program shape.


# --- sync_atom_on_loop -------------------------------------------------


def test_sync_atom_on_loop_passes_for_a_plain_scalar_query() -> None:
    """A bare Query has async affinity and is not in scope of the law."""
    assert_passes(Q())


def test_sync_atom_on_loop_passes_when_sync_only_atom_stays_off_loop() -> None:
    """A sync-only atom with no async-only sibling keeps the loop off."""
    assert_passes(SyncOnly())


def test_sync_atom_on_loop_fails_when_sync_only_atom_shares_tree_with_async_only() -> None:
    """Sequential inheritance puts every node on the loop once one branch is async-only."""
    assert_fails(FlowS(SyncCmd(R()), AsyncCmd(R())), "sync_atom_on_loop")


def test_sync_atom_on_loop_fires_as_warning() -> None:
    """The law surfaces at WARNING severity, not ERROR."""
    fired = [
        v for v in violations(FlowS(SyncCmd(R()), AsyncCmd(R()))) if v.law == "sync_atom_on_loop"
    ]
    assert fired
    assert all(v.severity is Severity.WARNING for v in fired)
