"""Literal: the constant-yielding ScalarQuery.

The trivial Query - an irreducible leaf that carries a value in its payload
and yields it once, pure (no effects). Most non-Ref leaves in a Nu program are
LiteralQuerys, so it gets its own module apart from the numeric ScalarQueries in
``arithmetic``.

``compile`` (sync hot path) and ``acompile`` (async hot path) each return a
thunk that closes over the payload value and returns it, ignoring the Runtime
and any children.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Literal"]


class Literal(ScalarQuery):
    """A ScalarQuery that yields a constant value carried in its payload."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self._payload = {"value": value}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value = self._payload["value"]

        def thunk(rt: Runtime) -> object:
            return value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value = self._payload["value"]

        async def athunk(rt: Runtime) -> object:
            return value

        return athunk

    def __repr__(self) -> str:
        return repr(self._payload["value"])
