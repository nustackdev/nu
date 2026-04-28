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

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


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


class AddCmd(ScalarQuery):
    """Add element to set: s.add(value). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"add() requires mutable set, got {type(a).__name__}")
        a.add(b)
        return None


class RemoveCmd(ScalarQuery):
    """Remove element from set: s.remove(value). Returns None, or INVALID if not found."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"remove() requires mutable set, got {type(a).__name__}")
        try:
            a.remove(b)
        except KeyError:
            return INVALID
        return None


class DiscardCmd(ScalarQuery):
    """Discard element from set: s.discard(value). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"discard() requires mutable set, got {type(a).__name__}")
        a.discard(b)
        return None


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


class SetUpdateCmd(ScalarQuery):
    """Update set with elements from other: s.update(other). Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"update() requires mutable set, got {type(a).__name__}")
        if not isinstance(b, Set):
            return INVALID
        a |= b
        return None


class IntersectionUpdateCmd(ScalarQuery):
    """Keep only elements found in both: s.intersection_update(other). Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"intersection_update() requires mutable set, got {type(a).__name__}")
        if not isinstance(b, Set):
            return INVALID
        a &= b
        return None


class DifferenceUpdateCmd(ScalarQuery):
    """Remove elements found in other: s.difference_update(other). Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(f"difference_update() requires mutable set, got {type(a).__name__}")
        if not isinstance(b, Set):
            return INVALID
        a -= b
        return None


class SymmetricDifferenceUpdateCmd(ScalarQuery):
    """Keep elements in either but not both: s.symmetric_difference_update(other). Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSet):
            raise TypeError(
                f"symmetric_difference_update() requires mutable set, got {type(a).__name__}"
            )
        if not isinstance(b, Set):
            return INVALID
        a ^= b
        return None
