"""Set interactions.

Reads (Query):
    Union, Intersection, Difference, SymmetricDifference
    IsSubset, IsSuperset, IsDisjoint
    Copy
    SetOr, SetAnd, SetSub, SetXor

Mutations that return nothing (Command):
    AddCmd, Remove, Discard
    SetUpdate, IntersectionUpdate, DifferenceUpdate,
    SymmetricDifferenceUpdate

Mutations that return a value (Action):
    SetPop (set.pop returns an arbitrary element)
    SetIOr, SetIAnd, SetISub, SetIXor (in-place operators return self)
"""

from __future__ import annotations

from collections.abc import MutableSet
from collections.abc import Set as ABCSet
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.factory import host
from nu.lang import Command, ScalarAction, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "AddCmd",
    "Copy",
    "Difference",
    "DifferenceUpdate",
    "Discard",
    "FrozenSetCreate",
    "FrozenSetOf",
    "Intersection",
    "IntersectionUpdate",
    "IsDisjoint",
    "IsSubset",
    "IsSuperset",
    "Remove",
    "SetAnd",
    "SetCreate",
    "SetIAnd",
    "SetIOr",
    "SetISub",
    "SetIXor",
    "SetOf",
    "SetOr",
    "SetPop",
    "SetSub",
    "SetUpdate",
    "SetXor",
    "SymmetricDifference",
    "SymmetricDifferenceUpdate",
    "Union",
]


# =============================================================================
# SET CONSTRUCTORS
# =============================================================================

# Empty set: deterministic (always set()), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two SetCreate results.
SetCreate = host(set, name="SetCreate")
# Empty frozenset: deterministic and immutable (sharing one frozenset() is fine).
FrozenSetCreate = host(frozenset, name="FrozenSetCreate")
# Set / FrozenSet from positional items: siblings to TupleOf / ListOf.
SetOf = host(lambda *items: set(items), name="SetOf")
FrozenSetOf = host(lambda *items: frozenset(items), name="FrozenSetOf")


def _as_set(value: object) -> object:
    """A set-like exposing the named set methods (``.union`` / ``.intersection`` / ...).

    Real ``set`` / ``frozenset`` keep their type and methods; other ABCSet
    instances (``dict_keys`` / ``dict_items`` / ``KeysView`` / ``ItemsView``)
    implement only the operators, so materialize them to ``set``.
    """
    return value if isinstance(value, (set, frozenset)) else set(value)  # type: ignore[arg-type]


# =============================================================================
# SET READS (Query): return new sets / bools, no mutation
# =============================================================================


class Union(ScalarQuery):
    """Set union: left.union(right). Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).union(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).union(b)

        return athunk


class Intersection(ScalarQuery):
    """Set intersection: left.intersection(right). Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).intersection(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).intersection(b)

        return athunk


class Difference(ScalarQuery):
    """Set difference: left.difference(right). Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).difference(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).difference(b)

        return athunk


class SymmetricDifference(ScalarQuery):
    """Set symmetric difference: left.symmetric_difference(right). Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).symmetric_difference(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet):
                return INVALID
            return _as_set(a).symmetric_difference(b)

        return athunk


class IsSubset(ScalarQuery):
    """Test if subset: left <= right. Returns a bool."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a <= b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a <= b

        return athunk


class IsSuperset(ScalarQuery):
    """Test if superset: left >= right. Returns a bool."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a >= b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a >= b

        return athunk


class IsDisjoint(ScalarQuery):
    """Test if disjoint: left.isdisjoint(right). Returns a bool."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a.isdisjoint(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a.isdisjoint(b)

        return athunk


class Copy(ScalarQuery):
    """Shallow copy: s.copy(). Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, ABCSet):
                return INVALID
            return obj.copy()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, ABCSet):
                return INVALID
            return obj.copy()

        return athunk


class SetOr(ScalarQuery):
    """Set union operator: left | right. Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a | b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a | b

        return athunk


class SetAnd(ScalarQuery):
    """Set intersection operator: left & right. Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a & b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a & b

        return athunk


class SetSub(ScalarQuery):
    """Set difference operator: left - right. Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a - b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a - b

        return athunk


class SetXor(ScalarQuery):
    """Set symmetric difference operator: left ^ right. Returns a new set."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a ^ b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, ABCSet) or not isinstance(b, ABCSet):
                return INVALID
            return a ^ b

        return athunk


# =============================================================================
# SET MUTATIONS: return nothing (Command)
# =============================================================================


class AddCmd(Command):
    """Add element to set: s.add(value). Mutates the set; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.add(value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.add(value)

        return athunk


class Remove(Command):
    """Remove element from set: s.remove(value). Mutates the set; returns nothing.

    Raises KeyError if the element is absent (Python parity).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.remove(value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.remove(value)

        return athunk


class Discard(Command):
    """Discard element from set: s.discard(value). Mutates the set; returns nothing.

    No error if the element is absent (Python parity).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.discard(value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.discard(value)

        return athunk


class SetUpdate(Command):
    """Update set with elements from other: s.update(other). Mutates the set; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target |= other

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target |= other

        return athunk


class IntersectionUpdate(Command):
    """Keep only elements found in both: s.intersection_update(other).

    Mutates the set; returns nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target &= other

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target &= other

        return athunk


class DifferenceUpdate(Command):
    """Remove elements found in other: s.difference_update(other). Mutates the set; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target -= other

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target -= other

        return athunk


class SymmetricDifferenceUpdate(Command):
    """Keep elements in either but not both: s.symmetric_difference_update(other).

    Mutates the set; returns nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target ^= other

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target ^= other

        return athunk


# =============================================================================
# SET MUTATIONS: mutate AND return a value (Action)
# =============================================================================


class SetPop(ScalarAction):
    """Pop arbitrary element: s.pop(). Mutates the set; returns the element.

    Returns INVALID if the set is empty (Python raises KeyError).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, MutableSet):
                raise TypeError(f"pop() requires mutable set, got {type(obj).__name__}")
            try:
                return obj.pop()
            except KeyError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, MutableSet):
                raise TypeError(f"pop() requires mutable set, got {type(obj).__name__}")
            try:
                return obj.pop()
            except KeyError:
                return INVALID

        return athunk


class SetIOr(ScalarAction):
    """In-place union: left |= right. Mutates the set; returns the set."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target |= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target |= other
            return target

        return athunk


class SetIAnd(ScalarAction):
    """In-place intersection: left &= right. Mutates the set; returns the set."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target &= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target &= other
            return target

        return athunk


class SetISub(ScalarAction):
    """In-place difference: left -= right. Mutates the set; returns the set."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target -= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target -= other
            return target

        return athunk


class SetIXor(ScalarAction):
    """In-place symmetric difference: left ^= right. Mutates the set; returns the set."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target ^= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target ^= other
            return target

        return athunk
