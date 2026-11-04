"""NULL atoms: the queries that know NULL by design.

``IsNull`` asks whether a value is NULL, and ``Fallback`` picks the first value
that is not. Every other atom runs plain Python and lets NULL's own interface
decide; these two observe it.

They live in core because the ``Form`` base exposes them on every form as
``is_null()`` / ``fallback()``. Sort: all ScalarQuery (Q).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import NULL, ScalarQuery, is_null


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "Fallback",
    "IsNull",
]


class IsNull(ScalarQuery):
    """True if its one child is NULL.

    Args:
        value: the value to test.

    Notes:
        - Asks about the value held, not the address: a container ref's value
          is a lazy handle and never NULL, so use ``exists()`` on refs.

    Yields:
        A plain bool.

    Example:
        >>> from nu.lang import NULL
        >>> nu.run(nu.IsNull(NULL))[0]
        True
        >>> nu.run(nu.IsNull(None))[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return is_null(only(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return is_null(await only(rt))

        return athunk


class Fallback(ScalarQuery):
    """The first of its children that is not NULL.

    Args:
        value: the value to keep when it is not NULL.
        *alternatives: tried in order while everything before them is NULL.

    Notes:
        - Checks NULL, not truthiness: ``0``, ``""``, ``False`` and ``None``
          are values and are kept.
        - Short-circuits: children after the first non-NULL one are never
          evaluated.
        - Reached as ``x.fallback(a, b, ...)`` on every Form, which also
          keeps the result in ``x``'s Form.

    Yields:
        The first non-NULL child. The last NULL when every child is NULL.

    Example:
        >>> from nu.lang import NULL
        >>> nu.run(nu.Fallback(NULL, 0, 5))[0]
        0
        >>> nu.run(nu.Fallback(NULL, NULL))[0]
        <NULL>
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            v: object = NULL
            for ct in children:
                v = ct(rt)
                if not is_null(v):
                    return v
            return v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            v: object = NULL
            for ct in children:
                v = await ct(rt)
                if not is_null(v):
                    return v
            return v

        return athunk
