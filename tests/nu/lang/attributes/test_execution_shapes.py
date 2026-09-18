"""Attribute correctness across tree shapes for the async-affinity axis.

Locks in per-node values of ``REQUIRES_ASYNC`` / ``ASYNC_AFFINITY`` /
``HAS_ASYNC_ONLY_ATOM`` / ``HAS_SYNC_ONLY_ATOM`` / ``ON_LOOP`` across the
shapes ``test_execution.py`` doesn't cover: mixed sync+async siblings, deeply
nested wrapping, folds through the async-only Strategy shapes (Race, AnyN),
and the trivial Ref baseline. Pins the compile-time answer the Runtime
scheduler reads.
"""

from __future__ import annotations

from _support.law_terms import FlowS, R

from nu.core.flows import AnyN, Parallel, Race, Sequential
from nu.engine.structure import Declared
from nu.lang import ScalarQuery
from nu.lang.attributes import Attr
from nu.lang.helpers import compile as nu_compile


class AsyncOnly(ScalarQuery):
    """A ScalarQuery that only runs async."""

    _requires_async = Declared(value=True, name="requires_async")


class SyncOnly(ScalarQuery):
    """A ScalarQuery with no async affinity."""

    async_affinity = Declared(value=False)


# --- REQUIRES_ASYNC / ASYNC_AFFINITY per-node in mixed trees -----------


def test_requires_async_is_per_atom_not_folded() -> None:
    program = nu_compile(Parallel(AsyncOnly(), SyncOnly()))
    assert program.attr((), Attr.REQUIRES_ASYNC) is False
    assert program.attr((0,), Attr.REQUIRES_ASYNC) is True
    assert program.attr((1,), Attr.REQUIRES_ASYNC) is False


def test_async_affinity_is_per_atom_not_folded() -> None:
    program = nu_compile(Parallel(AsyncOnly(), SyncOnly()))
    assert program.attr((), Attr.ASYNC_AFFINITY) is True
    assert program.attr((0,), Attr.ASYNC_AFFINITY) is True
    assert program.attr((1,), Attr.ASYNC_AFFINITY) is False


# --- HAS_ASYNC_ONLY_ATOM across shapes ---------------------------------


def test_has_async_only_atom_flat_parallel_root_true() -> None:
    program = nu_compile(Parallel(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_ASYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


def test_has_async_only_atom_deeply_nested_bubbles_to_root() -> None:
    program = nu_compile(FlowS(FlowS(FlowS(AsyncOnly()))))
    column = program.attrs[Attr.HAS_ASYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(0, 0)]] is True
    assert column[program.id_of[(0, 0, 0)]] is True


def test_has_async_only_atom_folds_through_race() -> None:
    program = nu_compile(Race(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_ASYNC_ONLY_ATOM]
    # Race itself declares requires_async=True, so its root is True on that
    # ground; the async-only child is True; the sync-only child is False.
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


def test_has_async_only_atom_folds_through_anyn() -> None:
    program = nu_compile(AnyN(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_ASYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


# --- HAS_SYNC_ONLY_ATOM across shapes ----------------------------------


def test_has_sync_only_atom_flat_parallel_root_true() -> None:
    program = nu_compile(Parallel(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_SYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is False
    assert column[program.id_of[(1,)]] is True


def test_has_sync_only_atom_deeply_nested_bubbles_to_root() -> None:
    program = nu_compile(FlowS(FlowS(FlowS(SyncOnly()))))
    column = program.attrs[Attr.HAS_SYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(0, 0)]] is True
    assert column[program.id_of[(0, 0, 0)]] is True


def test_has_sync_only_atom_folds_through_race() -> None:
    program = nu_compile(Race(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_SYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is False
    assert column[program.id_of[(1,)]] is True


def test_has_sync_only_atom_folds_through_anyn() -> None:
    program = nu_compile(AnyN(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.HAS_SYNC_ONLY_ATOM]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is False
    assert column[program.id_of[(1,)]] is True


# --- ON_LOOP across shapes ---------------------------------------------


def test_on_loop_parallel_mixed_branches_per_child() -> None:
    program = nu_compile(Parallel(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


def test_on_loop_sequential_mixed_hoists_loop_to_all_children() -> None:
    # Sequential is not per-child - the async-only child pins the parent True,
    # and the sync-only sibling inherits it too.
    program = nu_compile(Sequential(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is True


def test_on_loop_deeply_nested_async_only_reaches_the_root() -> None:
    program = nu_compile(FlowS(FlowS(FlowS(AsyncOnly()))))
    column = program.attrs[Attr.ON_LOOP]
    for path in [(), (0,), (0, 0), (0, 0, 0)]:
        assert column[program.id_of[path]] is True


def test_on_loop_race_children_resolve_per_child() -> None:
    program = nu_compile(Race(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    # Race is PARALLEL, so per-child resolution applies just like Parallel.
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


def test_on_loop_anyn_children_resolve_per_child() -> None:
    program = nu_compile(AnyN(AsyncOnly(), SyncOnly()))
    column = program.attrs[Attr.ON_LOOP]
    assert column[program.id_of[()]] is True
    assert column[program.id_of[(0,)]] is True
    assert column[program.id_of[(1,)]] is False


# --- trivial: bare Ref --------------------------------------------------


def test_bare_ref_carries_all_default_execution_attrs() -> None:
    program = nu_compile(R())
    assert program.attr((), Attr.REQUIRES_ASYNC) is False
    assert program.attr((), Attr.ASYNC_AFFINITY) is True
    assert program.attr((), Attr.HAS_ASYNC_ONLY_ATOM) is False
    assert program.attr((), Attr.HAS_SYNC_ONLY_ATOM) is False
    assert program.attr((), Attr.ON_LOOP) is False
