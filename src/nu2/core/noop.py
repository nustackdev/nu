"""Noop: the do-nothing leaf Query.

A childless, effect-free ScalarQuery that yields ``None``. It is the placeholder
for an absent optional branch - a ``catch`` / ``finally_`` slot that the author
left out, an else-less conditional - where the slot must still hold a Nu so the
structure stays fixed, but nothing should run there. Identity-checked by the
owner (``isinstance(child, Noop)``) and typically never executed.

Query-shaped for now: it slot-fits anywhere the composition matrix admits a
ScalarQuery (value slots, Span aux slots). A truly universal no-op accepted in
every slot - mutator bodies, param slots - would need the matrix to slot-fit it
the way it looks through a Span; that is a larger model change left for when
no-ops recur outside these placeholder uses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Noop"]


class Noop(ScalarQuery):
    """A ScalarQuery that does nothing and yields ``None``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return lambda rt: None

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> None:
            return None

        return athunk
