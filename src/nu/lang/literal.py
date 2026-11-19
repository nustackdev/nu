"""Literal: wraps a raw Python value as a Nu term.

The trivial Query - an irreducible leaf that carries a value as its one field
and yields it once, pure (no effects). Most non-Ref leaves in a Nu program are
Literals.

It lives in ``lang`` rather than with the atoms in ``nu.core`` because it is a
language primitive, not a mapping of a Python builtin: ``Nu.__init__`` wraps
every non-Nu child in one, so ``Add(1, 2)`` reads the same as
``Add(Literal(1), Literal(2))``. The language cannot construct a tree without
it.

Sorts: ScalarQuery (Q). No children: the value lives entirely in the ``value`` field.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk that closes over the value and returns it,
ignoring the Runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.kinds import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Literal"]


class Literal(ScalarQuery):
    """A constant value wrapped as a term.

    Args:
        value: the Python value to carry. Held as-is in the ``value`` field,
            never evaluated or copied. Anything goes: numbers, dicts, classes,
            functions, live objects, even a term (held as data, not run).

    Notes:
        - Any tree builder that gets a raw Python value where a term is
          expected wraps it in a Literal automatically.

    Yields:
        ``value``, unchanged, every time.

    Example:
        >>> nu.run(nu.Literal(42))[0]
        42
        >>> nu.run(nu.Literal("hi"))[0]
        'hi'
    """

    value: object
    """The carried Python value, as given."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value = self.value

        def thunk(rt: Runtime) -> object:
            return value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value = self.value

        async def athunk(rt: Runtime) -> object:
            return value

        return athunk
