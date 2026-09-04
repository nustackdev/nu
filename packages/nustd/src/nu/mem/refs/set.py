"""Dict set reference: unordered unique-element container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import MutableSetRef, Slot
from nu.forms import Any, Set

from .base import RefBase


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg


__all__ = [
    "SetRef",
]


T = TypeVar("T")


E = TypeVar("E")


class SetRef(MutableSetRef, RefBase[set[T]], Generic[T]):
    """A set slot in the dict substrate, holding one plain set of values.

    No descent: a set has no addresses, so there is no child ref to navigate
    to. Everything happens through the set calls - membership, the algebra
    (``union``, ``difference``, ...), and the in-place mutations.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored value is an ordinary set and a read hands back that live
          object, so elements must be hashable and iteration order is
          whatever Python gives.
        - In-place calls read the container first and do nothing when the
          slot is absent, so ``set`` an empty set before the first ``add``.
        - The declared element type is metadata; nothing coerces or rejects
          what is written.

    Yields:
        The stored set. EMPTY when the slot was never written.

    Example:
        >>> class Port(nu.Shape):
        ...     members = nu.mem.SetRef.slot(str)
        >>> ctx = nu.Context().bind(dict, {"members": {"a"}}, Port)
        >>> _ = nu.run(Port.members.add("b"), ctx)
        >>> sorted(nu.run(Port.members, ctx)[0])
        ['a', 'b']
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
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["item_type"] = item_type

    @classmethod
    def slot(cls, item_type: type[E]) -> SetRef[E]:
        """Declare a set slot holding elements of ``item_type``.

        Args:
            item_type: the Python type of the elements held.

        Notes:
            - ``members: SetRef[str]`` as an annotation declares the same
              slot.

        Example:
            class Port(Shape):
                members = SetRef.slot(str)
        """
        return Slot(cls, item_type=item_type)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``SetRef[T]``."""
        (item_type,) = args
        return {"item_type": item_type}
