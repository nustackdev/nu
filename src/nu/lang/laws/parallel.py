"""Parallel-family placement laws: forced-mode / child-affinity coherence.

``ParallelThreaded`` rejects any subtree that folds an async-only atom (its
forced thread path cannot host one). ``ParallelAsync`` rejects any subtree
that folds a sync-only atom.

Both laws scope by the parent's ``_FORCE_MODE`` class attribute (read from
``type(program.terms[nid])``) - only ``ParallelThreaded`` / ``ParallelAsync``
set this, so no import of the flow classes is needed and no cycle forms
between ``nu.lang.laws`` and ``nu.flows.parallel``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr


if TYPE_CHECKING:
    from nu.engine import Path, Program

__all__ = ["LAWS"]


def _is_forced(mode: str):  # noqa: ANN202
    """Return a Predicate scoping to nodes whose kind sets ``_FORCE_MODE == mode``."""

    @predicate
    def test(program: Program, path: Path) -> bool:
        term = program.terms[program.id_of[path]]
        return getattr(type(term), "_FORCE_MODE", None) == mode

    return test


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


LAWS: tuple[Law, ...] = (
    Law(
        "parallel_threaded_no_async_only_child",
        scope=_is_forced("threaded"),
        holds=_no_async_only_child,
        message=(
            "a ParallelThreaded holds an async-only child (the forced thread path cannot host it)"
        ),
    ),
    Law(
        "parallel_async_no_sync_only_child",
        scope=_is_forced("async"),
        holds=_no_sync_only_child,
        message="a ParallelAsync holds a sync-only child (the forced loop path cannot host it)",
    ),
)
