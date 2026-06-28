"""Logical atoms: Python's boolean operators and truthiness.

Maps Python's boolean operations onto Nu ScalarQueries. Pure compute; no
Context effect of their own.

Builtins / operators to cover (Python -> Nu):
- ``and`` -> ``AndQuery``, ``or`` -> ``OrQuery``, ``not`` -> ``NotQuery``
- ``bool`` (truthiness) -> ``BoolQuery``

Sorts: all ScalarQuery (Q). ``AndQuery`` / ``OrQuery`` are commutative + associative +
idempotent and variadic; ``NotQuery`` and ``BoolQuery`` are unary. ``logical`` owns
``BoolQuery``; ``cast`` does not define it.

AndQuery / OrQuery semantics: Python's ``and`` / ``or`` short-circuit and return an
operand (not a bool). Nu does not mirror that: these atoms coerce to ``bool``
and fold every operand eagerly,
so a Nu ``AndQuery`` / ``OrQuery`` always yields a plain boolean and sentinel
propagation gets the chance to fire on any branch. ``AndQuery`` yields ``True``
over no operands, ``OrQuery`` yields ``False``.

Sentinels: each operand is checked; an ``EMPTY`` or ``INVALID`` operand
collapses the whole query to ``INVALID`` (per ``nu2.lang.sentinels``).

v1 reference: ``src/nu/queries/logical.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["AndQuery", "BoolQuery", "NotQuery", "OrQuery"]


class AndQuery(ScalarQuery):
    """The conjunction of its boolean children. Yields ``True`` if empty."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out = True
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and bool(v)
            return out

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out = True
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and bool(v)
            return out

        return athunk


class OrQuery(ScalarQuery):
    """The disjunction of its boolean children. Yields ``False`` if empty."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out = False
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or bool(v)
            return out

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out = False
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or bool(v)
            return out

        return athunk


class NotQuery(ScalarQuery):
    """The negation of its one boolean child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return athunk


class BoolQuery(ScalarQuery):
    """The truthiness of its one child as a plain ``bool``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bool(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bool(v)

        return athunk
