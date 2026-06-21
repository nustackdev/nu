"""Set ops.

UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
IsSubsetOp, IsSupersetOp, IsDisjointOp
AddCmd, RemoveCmd, DiscardCmd
SetPopCmd, SetUpdateCmd
IntersectionUpdateCmd, DifferenceUpdateCmd, SymmetricDifferenceUpdateCmd
"""

from __future__ import annotations

from collections.abc import MutableSet, Set
from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "AddCmd",
    "DifferenceOp",
    "DifferenceUpdateCmd",
    "DiscardCmd",
    "IntersectionOp",
    "IntersectionUpdateCmd",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "RemoveCmd",
    "SetPopCmd",
    "SetUpdateCmd",
    "SymmetricDifferenceOp",
    "SymmetricDifferenceUpdateCmd",
    "UnionOp",
]


# =============================================================================
# SET OPERATIONS
# =============================================================================


class UnionOp(ScalarQuery):
    """Set union: left | right."""

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


class IntersectionOp(ScalarQuery):
    """Set intersection: left & right."""

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


class DifferenceOp(ScalarQuery):
    """Set difference: left - right."""

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


class SymmetricDifferenceOp(ScalarQuery):
    """Set symmetric difference: left ^ right."""

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


class IsSubsetOp(ScalarQuery):
    """Test if subset: left <= right."""

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


class IsSupersetOp(ScalarQuery):
    """Test if superset: left >= right."""

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


class IsDisjointOp(ScalarQuery):
    """Test if disjoint: left.isdisjoint(right)."""

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


# =============================================================================
# SET MUTATIONS
# =============================================================================


class AddCmd(ScalarQuery):
    """Add element to set: s.add(value); yields the set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.add(value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.add(value)
            return target

        return athunk


class RemoveCmd(ScalarQuery):
    """Remove element from set: s.remove(value); yields the set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.remove(value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.remove(value)
            return target

        return athunk


class DiscardCmd(ScalarQuery):
    """Discard element from set: s.discard(value); yields the set."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.discard(value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.discard(value)
            return target

        return athunk


class SetPopCmd(ScalarQuery):
    """Pop arbitrary element: s.pop(). Returns element, or INVALID if empty."""

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


class SetUpdateCmd(ScalarQuery):
    """Update set with elements from other: s.update(other); yields the set."""

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


class IntersectionUpdateCmd(ScalarQuery):
    """Keep only elements found in both: s.intersection_update(other); yields the set."""

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


class DifferenceUpdateCmd(ScalarQuery):
    """Remove elements found in other: s.difference_update(other); yields the set."""

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


class SymmetricDifferenceUpdateCmd(ScalarQuery):
    """Keep elements in either but not both: s.symmetric_difference_update(other); yields the set."""

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
