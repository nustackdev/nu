"""Act 3: emit the per-node thunk columns, children before parents.

Reverse-preorder walk over the index. Each Term's ``compile`` and
``acompile`` receive their precompiled child thunks and return the parent's,
capturing them in a closure. The reverse walk (``n - 1`` down to ``0``)
guarantees a child's thunk is in hand by the time its parent is compiled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .program import Program

__all__ = ["emit_thunks"]


def emit_thunks(program: Program) -> None:
    """Build the per-nid sync and async thunk columns on ``program``."""
    terms = program.terms
    children = program.children
    n = len(terms)
    thunks: list[Callable[[object], object]] = [None] * n  # type: ignore[list-item]
    athunks: list[Callable[[object], Awaitable[object]]] = [None] * n  # type: ignore[list-item]
    for nid in range(n - 1, -1, -1):
        child_nids = children[nid]
        child_thunks = tuple(thunks[c] for c in child_nids)
        child_athunks = tuple(athunks[c] for c in child_nids)
        term = terms[nid]
        thunks[nid] = term._compile(nid, child_thunks)
        athunks[nid] = term._acompile(nid, child_athunks)
    program.thunks = thunks
    program.athunks = athunks
