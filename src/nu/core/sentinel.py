"""Sentinel atoms: the queries that observe EMPTY.

The one core family that is not a Python builtin: ``IsEmpty`` / ``NotEmpty``
ask whether a value IS EMPTY, and ``Fallback`` picks the first value that is
not. Every other query propagates an EMPTY operand; these observe it, so they
are the only core atoms that do **not** guard - the compile thunk reads the
raw child value with no EMPTY short-circuit.

They live in core because they are reused everywhere (the ``Form`` base exposes
them as ``is_empty()`` / ``not_empty()`` / ``fallback()``, flows branch on them,
callers guard on them). Sort: all ScalarQuery (Q).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import EMPTY, ScalarQuery, is_empty


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "Fallback",
    "IsEmpty",
    "NotEmpty",
]


class IsEmpty(ScalarQuery):
    """True if its one child yields the EMPTY sentinel.

    Args:
        value: the value to test.

    Notes:
        - Accepts EMPTY rather than propagating it: this is one of the few
          core atoms that does not guard, since observing EMPTY is the whole
          point.

    Yields:
        A plain bool, never EMPTY.

    Example:
        >>> from nu.lang.sentinels import EMPTY
        >>> nu.run(nu.IsEmpty(EMPTY))[0]
        True
        >>> nu.run(nu.IsEmpty(5))[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return is_empty(only(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return is_empty(await only(rt))

        return athunk


class NotEmpty(ScalarQuery):
    """True if its one child does not yield EMPTY.

    Args:
        value: the value to test.

    Notes:
        - Accepts EMPTY rather than propagating it, same as :class:`IsEmpty`.

    Yields:
        A plain bool, never EMPTY.

    Example:
        >>> from nu.lang.sentinels import EMPTY
        >>> nu.run(nu.NotEmpty(EMPTY))[0]
        False
        >>> nu.run(nu.NotEmpty(5))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return not is_empty(only(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return not is_empty(await only(rt))

        return athunk


class Fallback(ScalarQuery):
    """The first of its children that is not EMPTY.

    Args:
        value: the value to keep when it is present.
        *alternatives: tried in order while everything before them is EMPTY.

    Notes:
        - Checks presence, not truthiness: ``0``, ``""``, ``False`` and
          ``None`` are present values and are kept.
        - Short-circuits: children after the first present one are never
          evaluated.
        - Reached as ``x.fallback(a, b, ...)`` on every Form, which also
          keeps the result in ``x``'s Form.

    Yields:
        The first present child. EMPTY only when every child is EMPTY.

    Example:
        >>> from nu.lang.sentinels import EMPTY
        >>> nu.run(nu.Fallback(EMPTY, 0, 5))[0]
        0
        >>> nu.run(nu.Fallback(EMPTY, EMPTY))[0]
        <EMPTY>
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            for ct in children:
                v = ct(rt)
                if v is not EMPTY:
                    return v
            return EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            for ct in children:
                v = await ct(rt)
                if v is not EMPTY:
                    return v
            return EMPTY

        return athunk
