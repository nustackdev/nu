"""Parallel-family placement laws.

These laws live in the flows layer (not ``nu.lang.laws``) so they can key on
the concrete Parallel classes by ``isinstance``, without ``nu.lang`` having
to import from ``nu.core.flows``. They are appended to ``nu.lang.laws.LAWS`` at
this package's import time - see ``nu.core.flows.parallel.__init__``.

Three rules:

- ``parallel_threaded_no_async_only_child``: ``ParallelThreaded`` cannot host
  a subtree that folds an async-only atom (its forced thread path is not on
  the loop).
- ``parallel_async_no_sync_only_child``: ``ParallelAsync`` cannot host a
  subtree that folds a sync-only atom (its forced loop path harms it).
- ``no_dynamic_under_smart_parallel``: base ``Parallel`` (no forced mode)
  cannot host any subtree carrying a Dyn. The smart-placement machinery
  needs statically-visible async affinity per child; Dyn's inner tree is not
  visible at compile time. The user must switch to ``ParallelThreaded`` /
  ``ParallelAsync`` to force a mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr

from .parallel import Parallel, ParallelAsync, ParallelThreaded


if TYPE_CHECKING:
    from nu.engine import Path, Program


__all__ = ["LAWS"]


@predicate
def _is_parallel_threaded(program: Program, path: Path) -> bool:
    return isinstance(program.terms[program.id_of[path]], ParallelThreaded)


@predicate
def _is_parallel_async(program: Program, path: Path) -> bool:
    return isinstance(program.terms[program.id_of[path]], ParallelAsync)


@predicate
def _is_smart_parallel(program: Program, path: Path) -> bool:
    """Base ``Parallel`` with no forced mode - the smart-placement variant."""
    term = program.terms[program.id_of[path]]
    return isinstance(term, Parallel) and not isinstance(term, (ParallelThreaded, ParallelAsync))


@predicate
def _no_async_only_child(program: Program, path: Path) -> bool:
    """Holds when no direct child of ``path`` folds an async-only atom."""
    nid = program.id_of[path]
    for child in program.children[nid]:
        if program.attr(program.path_of[child], Attr.HAS_ASYNC_ONLY_ATOM):
            return False
    return True


@predicate
def _no_sync_only_child(program: Program, path: Path) -> bool:
    """Holds when no direct child of ``path`` folds a sync-only atom."""
    nid = program.id_of[path]
    for child in program.children[nid]:
        if program.attr(program.path_of[child], Attr.HAS_SYNC_ONLY_ATOM):
            return False
    return True


@predicate
def _no_dynamic_in_subtree(program: Program, path: Path) -> bool:
    """Holds when no descendant of ``path`` (or itself) is a Dyn."""
    return not program.attr(path, Attr.HAS_DYNAMIC)


LAWS: tuple[Law, ...] = (
    Law(
        "parallel_threaded_no_async_only_child",
        scope=_is_parallel_threaded,
        holds=_no_async_only_child,
        message=(
            "a ParallelThreaded holds an async-only child (the forced thread path cannot host it)"
        ),
    ),
    Law(
        "parallel_async_no_sync_only_child",
        scope=_is_parallel_async,
        holds=_no_sync_only_child,
        message=("a ParallelAsync holds a sync-only child (the forced loop path cannot host it)"),
    ),
    Law(
        "no_dynamic_under_smart_parallel",
        scope=_is_smart_parallel,
        holds=_no_dynamic_in_subtree,
        message=(
            "smart Parallel cannot host a Dynamic child; "
            "use ParallelThreaded or ParallelAsync to force a mode"
        ),
    ),
)
