"""Literal: wraps a raw Python value as a Nu term.

The trivial Query - an irreducible leaf that carries a value in its payload
and yields it once, pure (no effects). Most non-Ref leaves in a Nu program are
Literals, so it gets its own module apart from the numeric ScalarQueries in
``arithmetic``.

Sorts: ScalarQuery (Q). No children: the value lives entirely in the payload.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk that closes over the payload value and returns it,
ignoring the Runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Literal"]


class Literal(ScalarQuery):
    """A constant value wrapped as a term.

    Args:
        value: the Python value to carry. Held as-is in the payload, never
            evaluated or copied.

    Notes:
        - Any tree builder that gets a raw Python value where a term is
          expected wraps it in a Literal automatically.

    Yields:
        ``value``, unchanged, every time. Never EMPTY or INVALID on its own -
        a Literal has no children to propagate a sentinel from.

    Example:
        >>> nu.run(nu.Literal(42))[0]
        42
        >>> nu.run(nu.Literal("hi"))[0]
        'hi'
    """

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
