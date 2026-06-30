"""Set ops.

UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
IsSubsetOp, IsSupersetOp, IsDisjointOp
AddCmd, RemoveCmd, DiscardCmd
SetPopCmd, SetUpdateCmd
IntersectionUpdateCmd, DifferenceUpdateCmd, SymmetricDifferenceUpdateCmd
"""

from __future__ import annotations

from collections.abc import MutableSet, Set
from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Effect, Mode


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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# SET OPERATIONS
# =============================================================================


class UnionOp(ScalarQuery):
    """Set union: left | right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a | b


class IntersectionOp(ScalarQuery):
    """Set intersection: left & right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a & b


class DifferenceOp(ScalarQuery):
    """Set difference: left - right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a - b


class SymmetricDifferenceOp(ScalarQuery):
    """Set symmetric difference: left ^ right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a ^ b


class IsSubsetOp(ScalarQuery):
    """Test if subset: left <= right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a <= b


class IsSupersetOp(ScalarQuery):
    """Test if superset: left >= right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a >= b


class IsDisjointOp(ScalarQuery):
    """Test if disjoint: left.isdisjoint(right)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Set) or not isinstance(b, Set):
            return INVALID
        return a.isdisjoint(b)


# =============================================================================
# SET MUTATIONS
# =============================================================================


class AddCmd(ScalarCommand):
    """Add element to set: s.add(value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(target).__name__}")
        target.add(value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(target).__name__}")
        target.add(value)


class RemoveCmd(ScalarCommand):
    """Remove element from set: s.remove(value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(target).__name__}")
        target.remove(value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(target).__name__}")
        target.remove(value)


class DiscardCmd(ScalarCommand):
    """Discard element from set: s.discard(value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(target).__name__}")
        target.discard(value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(target).__name__}")
        target.discard(value)


class SetPopCmd(ScalarQuery):
    """Pop arbitrary element: s.pop(). Returns element, or INVALID if empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, MutableSet):
            raise TypeError(f"pop() requires mutable set, got {type(operand).__name__}")
        try:
            return operand.pop()
        except KeyError:
            return INVALID


class SetUpdateCmd(ScalarCommand):
    """Update set with elements from other: s.update(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"update() requires mutable set, got {type(target).__name__}")
        if not isinstance(other, Set):
            raise TypeError(f"update() requires set, got {type(other).__name__}")
        target |= other

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(f"update() requires mutable set, got {type(target).__name__}")
        if not isinstance(other, Set):
            raise TypeError(f"update() requires set, got {type(other).__name__}")
        target |= other


class IntersectionUpdateCmd(ScalarCommand):
    """Keep only elements found in both: s.intersection_update(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"intersection_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(f"intersection_update() requires set, got {type(other).__name__}")
        target &= other

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"intersection_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(f"intersection_update() requires set, got {type(other).__name__}")
        target &= other


class DifferenceUpdateCmd(ScalarCommand):
    """Remove elements found in other: s.difference_update(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"difference_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(f"difference_update() requires set, got {type(other).__name__}")
        target -= other

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"difference_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(f"difference_update() requires set, got {type(other).__name__}")
        target -= other


class SymmetricDifferenceUpdateCmd(ScalarCommand):
    """Keep elements in either but not both: s.symmetric_difference_update(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"symmetric_difference_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(
                f"symmetric_difference_update() requires set, got {type(other).__name__}"
            )
        target ^= other

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSet):
            raise TypeError(
                f"symmetric_difference_update() requires mutable set, got {type(target).__name__}"
            )
        if not isinstance(other, Set):
            raise TypeError(
                f"symmetric_difference_update() requires set, got {type(other).__name__}"
            )
        target ^= other
