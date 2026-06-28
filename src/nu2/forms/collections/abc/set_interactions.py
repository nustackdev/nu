"""Set interactions.

Reads (Query):
    UnionQuery, IntersectionQuery, DifferenceQuery, SymmetricDifferenceQuery
    IsSubsetQuery, IsSupersetQuery, IsDisjointQuery
    CopyQuery
    SetOrQuery, SetAndQuery, SetSubQuery, SetXorQuery

Mutations that return nothing (Command):
    AddCommand, RemoveCommand, DiscardCommand
    SetUpdateCommand, IntersectionUpdateCommand, DifferenceUpdateCommand,
    SymmetricDifferenceUpdateCommand

Mutations that return a value (Action):
    SetPopAction (set.pop returns an arbitrary element)
    SetIOrAction, SetIAndAction, SetISubAction, SetIXorAction (in-place operators return self)
"""

from __future__ import annotations

from collections.abc import MutableSet, Set
from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarAction, ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "AddCommand",
    "CopyQuery",
    "DifferenceQuery",
    "DifferenceUpdateCommand",
    "DiscardCommand",
    "IntersectionQuery",
    "IntersectionUpdateCommand",
    "IsDisjointQuery",
    "IsSubsetQuery",
    "IsSupersetQuery",
    "RemoveCommand",
    "SetAndQuery",
    "SetIAndAction",
    "SetIOrAction",
    "SetISubAction",
    "SetIXorAction",
    "SetOrQuery",
    "SetPopAction",
    "SetSubQuery",
    "SetUpdateCommand",
    "SetXorQuery",
    "SymmetricDifferenceQuery",
    "SymmetricDifferenceUpdateCommand",
    "UnionQuery",
]


# =============================================================================
# SET READS (Query) — return new sets / bools, no mutation
# =============================================================================


class UnionQuery(ScalarQuery):
    """Set union: left.union(right). Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a | b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a | b

        return athunk


class IntersectionQuery(ScalarQuery):
    """Set intersection: left.intersection(right). Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a & b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a & b

        return athunk


class DifferenceQuery(ScalarQuery):
    """Set difference: left.difference(right). Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a - b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a - b

        return athunk


class SymmetricDifferenceQuery(ScalarQuery):
    """Set symmetric difference: left.symmetric_difference(right). Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a ^ b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a ^ b

        return athunk


class IsSubsetQuery(ScalarQuery):
    """Test if subset: left <= right. Returns a bool."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a <= b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a <= b

        return athunk


class IsSupersetQuery(ScalarQuery):
    """Test if superset: left >= right. Returns a bool."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a >= b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a >= b

        return athunk


class IsDisjointQuery(ScalarQuery):
    """Test if disjoint: left.isdisjoint(right). Returns a bool."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a.isdisjoint(b)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a.isdisjoint(b)

        return athunk


class CopyQuery(ScalarQuery):
    """Shallow copy: s.copy(). Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Set):
                return INVALID
            return obj.copy()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Set):
                return INVALID
            return obj.copy()

        return athunk


class SetOrQuery(ScalarQuery):
    """Set union operator: left | right. Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a | b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a | b

        return athunk


class SetAndQuery(ScalarQuery):
    """Set intersection operator: left & right. Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a & b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a & b

        return athunk


class SetSubQuery(ScalarQuery):
    """Set difference operator: left - right. Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a - b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a - b

        return athunk


class SetXorQuery(ScalarQuery):
    """Set symmetric difference operator: left ^ right. Returns a new set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a ^ b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Set) or not isinstance(b, Set):
                return INVALID
            return a ^ b

        return athunk


# =============================================================================
# SET MUTATIONS — return nothing (Command)
# =============================================================================


class AddCommand(Command):
    """Add element to set: s.add(value). Mutates the set; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class RemoveCommand(Command):
    """Remove element from set: s.remove(value). Mutates the set; returns nothing.

    Raises KeyError if the element is absent (Python parity).
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class DiscardCommand(Command):
    """Discard element from set: s.discard(value). Mutates the set; returns nothing.

    No error if the element is absent (Python parity).
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetUpdateCommand(Command):
    """Update set with elements from other: s.update(other). Mutates the set; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class IntersectionUpdateCommand(Command):
    """Keep only elements found in both: s.intersection_update(other).

    Mutates the set; returns nothing.
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class DifferenceUpdateCommand(Command):
    """Remove elements found in other: s.difference_update(other). Mutates the set; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SymmetricDifferenceUpdateCommand(Command):
    """Keep elements in either but not both: s.symmetric_difference_update(other).

    Mutates the set; returns nothing.
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
# SET MUTATIONS — mutate AND return a value (Action)
# =============================================================================


class SetPopAction(ScalarAction):
    """Pop arbitrary element: s.pop(). Mutates the set; returns the element.

    Returns INVALID if the set is empty (Python raises KeyError).
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetIOrAction(ScalarAction):
    """In-place union: left |= right. Mutates the set; returns the set."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetIAndAction(ScalarAction):
    """In-place intersection: left &= right. Mutates the set; returns the set."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetISubAction(ScalarAction):
    """In-place difference: left -= right. Mutates the set; returns the set."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetIXorAction(ScalarAction):
    """In-place symmetric difference: left ^= right. Mutates the set; returns the set."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
