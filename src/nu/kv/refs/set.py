"""Virtuals set reference: unordered unique-element container backed by a View."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import ReactiveSetRef, Slot
from nu.forms import Any, Set

from .base import ViewRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg
    from virtuals.collections import MutableSetBase


__all__ = [
    "SetRef",
]


T = TypeVar("T")


E = TypeVar("E")


class SetRef(ReactiveSetRef, ViewRef[set[T]], Generic[T]):
    """A set slot in KV storage: unordered, unique elements, stored decomposed.

    Notes:
        - Ops run against the live View, so membership and size are answered
          by storage rather than by reading the set out.
        - Elements have no addresses of their own to descend into: a set has
          no keys, so there is no element ref and no subscript.
        - The set algebra (``union``, ``intersection``, ...) yields values;
          the in-place variants (``update``, ``difference_update``, ...) are
          the ones that write.
        - Change observation covers the child, the children and the whole
          subtree, each with its own hook.
        - PrimitiveSetRef is the other choice: one opaque blob written whole.

    Example:
        class Portfolio(Shape):
            members = SetRef.slot(str)
        run(Portfolio.members.add("gor"), ctx)
        run(Portfolio.members.contains("gor"), ctx)
    """

    def _wrap_result(self, op: Nu) -> Set[T]:
        """Wrap a set-level op result as a Set."""
        return Set(op)

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        return Set(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        item_type: type[T],
        view_type: type[MutableSetBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["item_type"] = item_type

    @classmethod
    def slot(cls, item_type: type[E], view_type: type[MutableSetBase] | None = None) -> SetRef[E]:
        """Declare a set slot holding elements of ``item_type``."""
        from virtuals.views import SetView

        return Slot(cls, item_type=item_type, view_type=view_type or SetView)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``SetRef[T]``."""
        from virtuals.views import SetView

        (item_type,) = args
        return {"item_type": item_type, "view_type": SetView}
