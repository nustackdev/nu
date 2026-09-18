"""Logical atoms: Python's boolean operators and truthiness.

Maps Python's boolean operations onto Nu ScalarQueries. Pure compute; no
Context effect of their own.

Builtins / operators to cover (Python -> Nu):
- ``and`` -> ``And``, ``or`` -> ``Or``, ``not`` -> ``Not``
- ``bool`` (truthiness) -> ``ToBool``

Sorts: all ScalarQuery (Q). ``And`` / ``Or`` are variadic; ``Not`` and
``ToBool`` are unary. ``logical`` owns ``ToBool``; ``cast`` does not define it.

And / Or semantics: Python's ``and`` / ``or`` short-circuit and return an
operand (not a bool). Nu short-circuits the same way but always coerces to
``bool``, so a Nu ``And`` / ``Or`` yields a plain boolean while leaving the
operands past the deciding one unevaluated. That is what makes them usable
as guards: ``And(not_empty(x), contains(x))`` never runs ``contains`` when
``x`` is empty. ``And`` yields ``True`` over no operands, ``Or`` yields
``False``.

Sentinels: every operand that is actually evaluated is checked; an ``EMPTY``
or ``INVALID`` operand collapses the whole query to ``INVALID`` (per
``nu.lang.sentinels``). Short-circuit wins over sentinel poisoning - an
operand that is never evaluated can never poison the result.
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
    """The conjunction of its boolean children, each coerced with ``bool``.

    Args:
        *children: the values to conjoin.

    Notes:
        - Short-circuits like Python's ``and``: the first falsy child
          decides the result and the children after it are never
          evaluated. This is what lets ``And`` guard - a guard that still
          runs the thing it is guarding is not a guard.
        - Short-circuit beats sentinel poisoning: a child that is never
          evaluated never contributes its sentinel, so
          ``And(False, <INVALID>)`` is ``False``, not INVALID.
        - No children at all yields True.

    Yields:
        A plain bool. INVALID when an evaluated child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.And(True, True))[0]
        True
        >>> nu.run(nu.And(True, False))[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not builtins.bool(v):
                    return False
            return True

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not builtins.bool(v):
                    return False
            return True

        return athunk


class Or(ScalarQuery):
    """The disjunction of its boolean children, each coerced with ``bool``.

    Args:
        *children: the values to disjoin.

    Notes:
        - Short-circuits like Python's ``or``: the first truthy child
          decides the result and the children after it are never
          evaluated. This is what lets ``Or`` guard - a guard that still
          runs the thing it is guarding is not a guard.
        - Short-circuit beats sentinel poisoning: a child that is never
          evaluated never contributes its sentinel, so
          ``Or(True, <INVALID>)`` is ``True``, not INVALID.
        - No children at all yields False.

    Yields:
        A plain bool. INVALID when an evaluated child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Or(False, True))[0]
        True
        >>> nu.run(nu.Or(False, False))[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                if builtins.bool(v):
                    return True
            return False

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                if builtins.bool(v):
                    return True
            return False

        return athunk


class Not(ScalarQuery):
    """The negation of its one child.

    Args:
        value: the value to negate.

    Yields:
        A plain bool. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Not(True))[0]
        False
    """

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
    """The truthiness of its one child.

    Args:
        value: the value to coerce.

    Yields:
        A plain bool. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.core.logical.ToBool(0))[0]
        False
    """

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
    """Coerce ``x`` to a Nu ``Bool`` term.

    Args:
        x: the value to coerce.

    Notes:
        - ``Bool(ToBool(x))`` in one call: Form-wraps the raw ``ToBool``
          atom so the result composes like any other Nu term.

    Yields:
        A Nu ``Bool``.

    Example:
        >>> nu.run(nu.core.logical.bool(1))[0]
        True
    """
    from nu.forms.primitives import Bool

    return Bool(ToBool(x))
