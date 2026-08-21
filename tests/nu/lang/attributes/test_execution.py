"""Unit tests for ``nu.lang.attributes.execution``.

Covers the ``ExecOrder`` enum, declared / synthesized async-related
attributes (``REQUIRES_ASYNC``, ``ASYNC_AFFINITY``, ``HAS_ASYNC_ONLY_ATOM``,
``ON_LOOP``), and the inherited ``EXEC_ORDER`` threading.
"""

from __future__ import annotations

from _support.law_terms import Brk, Cmd, FlowS, Pol, Q, R

from nu.engine.structure import Declared
from nu.lang import ScalarQuery, Strategy
from nu.lang import compile as nu_compile
from nu.lang.attributes import Attr, ExecOrder


# --- inline dimension-local shapes --------------------------------------


class AsyncOnly(ScalarQuery):
    """A ScalarQuery that only runs async."""

    _requires_async = Declared(value=True, name="requires_async")


class SyncOnly(ScalarQuery):
    """A ScalarQuery with no async affinity."""

    async_affinity = Declared(value=False)


class FlowPar(Strategy):
    """A Strategy that runs its children in parallel."""

    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")


# --- helpers ------------------------------------------------------------


def _attr_at(term: object, attr: Attr, path: tuple[int, ...] = ()) -> object:
    program = nu_compile(term)
    nid = program.id_of[path]
    return program.attrs[attr][nid]


# --- ExecOrder enum -----------------------------------------------------


def test_exec_order_values() -> None:
    assert ExecOrder.SEQUENTIAL.value == "sequential"
    assert ExecOrder.PARALLEL.value == "parallel"


# --- declared defaults --------------------------------------------------


def test_requires_async_default_false_on_bare_query() -> None:
    program = nu_compile(Q())
    assert program.attr((), Attr.REQUIRES_ASYNC) is False


def test_async_affinity_default_true_on_bare_query() -> None:
    program = nu_compile(Q())
    assert program.attr((), Attr.ASYNC_AFFINITY) is True


def test_exec_order_default_sequential_on_strategy() -> None:
    program = nu_compile(FlowS(Cmd(R())))
    assert program.attr((), Attr.EXEC_ORDER) is ExecOrder.SEQUENTIAL


# --- declared overrides -------------------------------------------------


def test_requires_async_override_reads_true() -> None:
    program = nu_compile(AsyncOnly())
    assert program.attr((), Attr.REQUIRES_ASYNC) is True


def test_async_affinity_override_reads_false() -> None:
    program = nu_compile(SyncOnly())
    assert program.attr((), Attr.ASYNC_AFFINITY) is False


def test_exec_order_override_reads_parallel() -> None:
    program = nu_compile(FlowPar(SyncOnly(), AsyncOnly()))
    assert program.attr((), Attr.EXEC_ORDER) is ExecOrder.PARALLEL


# --- has_async_only_atom fold ------------------------------------------


def test_has_async_only_atom_false_on_bare_query() -> None:
    assert _attr_at(Q(), Attr.HAS_ASYNC_ONLY_ATOM) is False


def test_has_async_only_atom_true_on_async_only_atom() -> None:
    assert _attr_at(AsyncOnly(), Attr.HAS_ASYNC_ONLY_ATOM) is True


def test_has_async_only_atom_propagates_up_through_query() -> None:
    assert _attr_at(Q(AsyncOnly()), Attr.HAS_ASYNC_ONLY_ATOM) is True


def test_has_async_only_atom_true_at_root_under_strategy() -> None:
    assert _attr_at(FlowS(Cmd(R()), AsyncOnly()), Attr.HAS_ASYNC_ONLY_ATOM) is True


# --- has_sync_only_atom fold -------------------------------------------


def test_has_sync_only_atom_false_on_bare_query() -> None:
    assert _attr_at(Q(), Attr.HAS_SYNC_ONLY_ATOM) is False


def test_has_sync_only_atom_true_on_sync_only_atom() -> None:
    assert _attr_at(SyncOnly(), Attr.HAS_SYNC_ONLY_ATOM) is True


def test_has_sync_only_atom_propagates_up_through_query() -> None:
    assert _attr_at(Q(SyncOnly()), Attr.HAS_SYNC_ONLY_ATOM) is True


# --- async folds through Span transparency ------------------------------


def test_has_async_only_atom_propagates_through_span() -> None:
    """An async-only atom under a Span surfaces on the Span node."""
    assert _attr_at(Brk(AsyncOnly()), Attr.HAS_ASYNC_ONLY_ATOM) is True


def test_has_sync_only_atom_propagates_through_span() -> None:
    """A sync-only atom under a Span surfaces on the Span node."""
    assert _attr_at(Pol(SyncOnly()), Attr.HAS_SYNC_ONLY_ATOM) is True


# --- on_loop at the root ------------------------------------------------


def test_on_loop_false_at_root_when_no_async_only() -> None:
    assert _attr_at(FlowS(Cmd(R())), Attr.ON_LOOP) is False


def test_on_loop_true_at_root_when_subtree_has_async_only() -> None:
    assert _attr_at(FlowS(Cmd(R()), AsyncOnly()), Attr.ON_LOOP) is True


# --- on_loop sequential inheritance -------------------------------------


def test_on_loop_sequential_passthrough_hoists_loop_to_all_children() -> None:
    program = nu_compile(FlowS(Cmd(R()), AsyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is True


def test_on_loop_sequential_false_passthrough_when_no_async_only() -> None:
    program = nu_compile(FlowS(Cmd(R())))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is False
    assert column[program.id_of[(0,)]] is False


# --- on_loop parallel per-child resolution ------------------------------


def test_on_loop_parallel_branches_per_child() -> None:
    program = nu_compile(FlowPar(SyncOnly(), AsyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is False
    assert column[program.id_of[(1,)]] is True


def test_on_loop_parallel_portable_child_inherits_parent() -> None:
    program = nu_compile(FlowPar(Q(), AsyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is True
