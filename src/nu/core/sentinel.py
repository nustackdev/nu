"""Sentinel atoms: the predicates that observe EMPTY / INVALID.

The one core family that is not a Python builtin: ``IsEmpty`` / ``IsInvalid``
(and their negations) ask whether a value IS one of Nu's sentinels. Every other
atom propagates a sentinel operand; these observe it, so they are the only core
atoms that do **not** guard - the compile thunk runs the predicate on the raw
child value with no EMPTY / INVALID short-circuit.

They live in core because they are reused everywhere (the ``Form`` base exposes
them as ``is_empty()`` / ``is_invalid()``, flows branch on them, callers guard
on them). Sort: all ScalarQuery (Q).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery, is_empty, is_invalid


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "IsEmpty",
    "IsInvalid",
    "NotEmpty",
    "NotInvalid",
]


class IsEmpty(ScalarQuery):
    """True if its one child yields the EMPTY sentinel (accepts sentinels)."""

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
    """True if its one child does not yield EMPTY (accepts sentinels)."""

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


class IsInvalid(ScalarQuery):
    """True if its one child yields the INVALID sentinel (accepts sentinels)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return is_invalid(only(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return is_invalid(await only(rt))

        return athunk


class NotInvalid(ScalarQuery):
    """True if its one child does not yield INVALID (accepts sentinels)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return not is_invalid(only(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return not is_invalid(await only(rt))

        return athunk
