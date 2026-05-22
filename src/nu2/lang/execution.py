"""Execution concern: sync vs async, event-loop placement, and exec order.

A sort declares two bools: ``requires_async`` (the atom holds an async-only
operation, so it must run on a loop) and ``async_affinity`` (the atom suits an
async context). ``has_async_only_atom`` and ``has_sync_only_atom`` fold whether
a subtree forces or refuses an event loop; ``on_loop`` threads loop placement
down from the root, resolving per child under a parallel Flow. ``exec_order``
declares whether a Flow runs its children in sequence or in parallel.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang.attrs import Attr


if TYPE_CHECKING:
    from nu2.engine.attribution import AttributedTerm
    from nu2.engine.attribution.attributed_term import Path

__all__ = ["ATTRIBUTES", "ExecOrder"]


class ExecOrder(StrEnum):
    """Whether a Flow runs its children in sequence or in parallel."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


def _async_only(program: AttributedTerm, path: Path) -> bool:
    """A node's sort requires async, so it requires a loop."""
    return program.attr(path, Attr.REQUIRES_ASYNC)


def _sync_only(program: AttributedTerm, path: Path) -> bool:
    """A node's sort has no async affinity, so it belongs off a loop."""
    return not program.attr(path, Attr.ASYNC_AFFINITY)


def _any(own: bool, kids: list[bool]) -> bool:
    """Fold a flag up a subtree by disjunction."""
    return own or any(kids)


def _on_loop_root(program: AttributedTerm, path: Path) -> bool:
    """The root runs on a loop exactly when its subtree holds an async-only atom."""
    return program.attr(path, Attr.HAS_ASYNC_ONLY_ATOM)


def _on_loop_derive(program: AttributedTerm, parent: Path, slot: int, inherited: bool) -> bool:
    """Thread on_loop down; resolve per-child under a parallel parent.

    A sequential parent passes its value straight through. A parallel Flow
    resolves each child on its own subtree: an async-only child goes on the
    loop, a sync-only child goes off it, a portable child inherits.
    """
    if program.attr(parent, Attr.EXEC_ORDER) is not ExecOrder.PARALLEL:
        return inherited
    child = (*parent, slot)
    if program.attr(child, Attr.HAS_ASYNC_ONLY_ATOM):
        return True
    if program.attr(child, Attr.HAS_SYNC_ONLY_ATOM):
        return False
    return inherited


ATTRIBUTES: tuple[Attribute, ...] = (
    Attribute.declared(value=False, name=Attr.REQUIRES_ASYNC),
    Attribute.declared(value=True, name=Attr.ASYNC_AFFINITY),
    Attribute.declared(ExecOrder.SEQUENTIAL, name=Attr.EXEC_ORDER),
    Attribute.synthesized(
        Attr.HAS_ASYNC_ONLY_ATOM,
        base=_async_only,
        combine=_any,
        reads=(Attr.REQUIRES_ASYNC,),
    ),
    Attribute.synthesized(
        Attr.HAS_SYNC_ONLY_ATOM,
        base=_sync_only,
        combine=_any,
        reads=(Attr.ASYNC_AFFINITY,),
    ),
    Attribute.inherited(
        Attr.ON_LOOP,
        root=_on_loop_root,
        derive=_on_loop_derive,
        reads=(Attr.HAS_ASYNC_ONLY_ATOM, Attr.HAS_SYNC_ONLY_ATOM, Attr.EXEC_ORDER),
    ),
)
