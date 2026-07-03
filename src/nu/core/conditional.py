"""Conditional atoms: value-yielding branch selection.

Maps Python's conditional expression (``x if cond else y``) onto a Nu
ScalarQuery. Pure compute; no Context effect of its own. Sibling to the
mutating ``IfDo`` in ``nu.flows.control`` - same name family, different sort:
``IfDo`` runs one of two bodies for effect and yields nothing; ``IfQuery``
yields one of two values and mutates nothing.

Sorts: ScalarQuery (Q). Ternary (three children: cond, then, else_).

Short-circuit: only the taken branch is evaluated - matches Python's
conditional expression, and lets ``IfQuery(cond, safe, unsafe)`` guard the
``unsafe`` branch from firing when ``cond`` is truthy.

Sentinels: an ``EMPTY`` or ``INVALID`` condition collapses to ``INVALID``
(per ``nu.lang.sentinels``); an ``EMPTY`` / ``INVALID`` result on the taken
branch propagates through as ``INVALID``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["IfQuery"]


class IfQuery(ScalarQuery):
    """``IfQuery(cond, then, else_)`` - yield ``then`` if ``cond`` truthy, else ``else_``.

    Children: ``[cond, then, else_]``. Short-circuits: only the taken branch
    is evaluated.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, then_, else_ = children

        def thunk(rt: Runtime) -> object:
            c = cond(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            v = then_(rt) if c else else_(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return v

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, then_, else_ = children

        async def athunk(rt: Runtime) -> object:
            c = await cond(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            v = await (then_(rt) if c else else_(rt))
            if v is EMPTY or v is INVALID:
                return INVALID
            return v

        return athunk
