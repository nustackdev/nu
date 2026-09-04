"""Virtuals sequence reference: ordered container backed by a virtuals View."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import ReactiveSequenceRef, Slot
from nu.forms import Any, Iterator, List
from nu.lang.typeinfo import value_type_for

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg
    from virtuals.collections import MutableSequenceBase


__all__ = [
    "ListRef",
]


T = TypeVar("T")


E = TypeVar("E")


class ListRef(ReactiveSequenceRef["ItemRef"], ViewRef[list[T]], Generic[T]):
    """An ordered list slot in KV storage, decomposed into per-index children.

    Every element lives at its own address under the slot, so the list can be
    appended to, indexed and watched without reading the whole thing. The
    element type is fixed at declaration, and indexing descends to a leaf ref
    of that type rather than to a plain value.

    Notes:
        - Ops run against the live View, so ``len`` and ``contains`` are
          answered by storage instead of by materializing the list.
        - Indexing yields a leaf ref, which is what makes
          ``ref[0].set(...)`` and ``ref[0].on_change()`` possible.
        - Slices stay materialized: a slice is a value, not a ref.
        - A position does not vivify: writing at an index the list does not
          reach raises IndexError, so append before assigning. Reading an
          out-of-range index yields EMPTY instead.
        - Change observation covers the child, the children and the whole
          subtree, each with its own hook.
        - PrimitiveListRef is the other choice: one opaque blob, no
          per-element addresses, but heterogeneous contents.

    Example:
        class Portfolio(Shape):
            tags = ListRef.slot(str)
        run(Portfolio.tags.append("core"), ctx)
        run(Portfolio.tags[0], ctx)
    """

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """Navigate to the element at ``address`` as a substrate-backed virtuals ItemRef."""
        return ItemRef(
            address,
            value_type=self._payload["item_type"],
            value_value_type=self._payload["item_value_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> List[T]:
        """Wrap a sequence-level op result as a List."""
        return List(op)

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        return Iterator(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> List[T]:
        return List(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        item_type: type[T],
        item_value_type: type,
        view_type: type[MutableSequenceBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["item_type"] = item_type
        self._payload["item_value_type"] = item_value_type

    @classmethod
    def slot(
        cls, item_type: type[E], view_type: type[MutableSequenceBase] | None = None
    ) -> ListRef[E]:
        """Declare a list slot holding elements of ``item_type``."""
        from virtuals.views import ListView

        return Slot(
            cls,
            item_type=item_type,
            item_value_type=value_type_for(item_type),
            view_type=view_type or ListView,
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ListRef[T]``."""
        from virtuals.views import ListView

        (item_type,) = args
        return {
            "item_type": item_type,
            "item_value_type": value_type_for(item_type),
            "view_type": ListView,
        }
