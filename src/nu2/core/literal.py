"""Literal: the constant-yielding ScalarQuery.

The trivial Query - an irreducible leaf that carries a value in its payload
and yields it once, pure (no effects). Most non-Ref leaves in a Nu program are
Literals, so it gets its own module apart from the numeric ScalarQueries in
``arithmetic``.

``compile`` (sync hot path) and ``acompile`` (async hot path) each return a
thunk that closes over the payload value and returns it, ignoring the Runtime
and any children.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Literal"]


class Literal(ScalarQuery):
    """A ScalarQuery that yields a constant value carried in its payload."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.payload = {"value": value}

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        value = self.payload["value"]

        def thunk(rt: Runtime) -> object:
            return value

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        value = self.payload["value"]

        async def athunk(rt: Runtime) -> object:
            return value

        return athunk
