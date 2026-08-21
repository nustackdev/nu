"""Logical atoms: Python's boolean operators and truthiness.

Maps Python's boolean operations onto Nu ScalarQueries. Pure compute; no
Context effect of their own.

Builtins / operators to cover (Python -> Nu):
- ``and`` -> ``And``, ``or`` -> ``Or``, ``not`` -> ``Not``
- ``bool`` (truthiness) -> ``ToBool``

Sorts: all ScalarQuery (Q). ``And`` / ``Or`` are variadic; ``Not`` and
``ToBool`` are unary. ``logical`` owns ``ToBool``; ``cast`` does not define it.

And / Or semantics: Python's ``and`` / ``or`` short-circuit and return an
operand (not a bool). Nu does not mirror that: these atoms coerce to ``bool``
and fold every operand eagerly,
so a Nu ``And`` / ``Or`` always yields a plain boolean and sentinel
propagation gets the chance to fire on any branch. ``And`` yields ``True``
over no operands, ``Or`` yields ``False``.

Sentinels: each operand is checked; an ``EMPTY`` or ``INVALID`` operand
collapses the whole query to ``INVALID`` (per ``nu.lang.sentinels``).
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["And", "Not", "Or", "ToBool", "bool"]


class And(ScalarQuery):
    """The conjunction of its boolean children. Yields ``True`` if empty."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out = True
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and builtins.bool(v)
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out = True
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and builtins.bool(v)
            return out

        return athunk


class Or(ScalarQuery):
    """The disjunction of its boolean children. Yields ``False`` if empty."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out = False
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or builtins.bool(v)
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out = False
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or builtins.bool(v)
            return out

        return athunk


class Not(ScalarQuery):
    """The negation of its one boolean child."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return athunk


class ToBool(ScalarQuery):
    """The truthiness of its one child as a plain ``bool``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.bool(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.bool(v)

        return athunk


# --- wrappers: coerce + tag as a Form (the user-facing surface) ------------


def bool(x: object) -> object:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Bool`` term. ``Bool(ToBool(x))`` in one call."""
    from nu.forms.primitives import Bool

    return Bool(ToBool(x))
