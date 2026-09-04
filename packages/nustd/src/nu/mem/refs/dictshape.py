"""Dict shapes dict reference: mapping of homogeneous shapes.

Key descent (``ref[k]``) is the blueprint's ``__getitem__``: it returns a
``ShapeRef`` at the key with this ref as ``parent_ref``. The value shape type is
passed to the blueprint as ``item_shape_type``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import MutableShapesMappingRef, Slot
from nu.forms import Any, Dict, DictItems, DictKeys, DictValues, Iterator
from nu.lang.typeinfo import value_type_for

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg


__all__ = [
    "ShapesDictRef",
]


K = TypeVar("K")
T = TypeVar("T", bound="Shape")


DK = TypeVar("DK")
S = TypeVar("S", bound="Shape")


class ShapesDictRef(MutableShapesMappingRef[T], RefBase[dict[K, dict]], Generic[K, T]):
    """A keyed collection of one Shape's records, stored as a dict of dicts.

    Subscripting descends: ``ref[k]`` is a ``ShapeRef`` at that key holding
    the value Shape, so ``users["ada"].name`` is a path down to a leaf and
    nothing is read until the whole chain runs. The mapping calls on the ref
    itself act on the outer dict.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Values are plain dicts, so a record is added by writing a dict, not
          a Shape instance.
        - Writing through a key creates the outer dict and the record on the
          way down; the whole-container calls (``keys``, ``update``, ...)
          instead do nothing while the slot is absent.

    Yields:
        The stored dict of inner dicts. EMPTY when the slot was never
        written.

    Example:
        >>> class User(nu.Shape):
        ...     name = nu.mem.StrRef.slot()
        >>> class Team(nu.Shape):
        ...     users = nu.mem.ShapesDictRef.slot(User)
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Team)
        >>> _ = nu.run(Team.users["ada"].name.set("Ada"), ctx)
        >>> data
        {'users': {'ada': {'name': 'Ada'}}}
    """

    def _wrap_item_ref(self, address: object) -> ShapeRef:
        """Navigate to the shape at ``address`` as a substrate-backed mem ShapeRef."""
        return ShapeRef(
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> Dict:
        """Wrap a mapping-level op result as a Dict."""
        return Dict(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        return DictItems(operand)

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        return Iterator(operand)

    def _wrap_value_result(self, operand: Nu) -> Any:
        return Any(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        shape_type: type[T],
        key_type: type[K],
        key_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._payload["value_type"] = dict
        self._payload["key_type"] = key_type
        self._payload["key_value_type"] = key_value_type

    @classmethod
    def slot(cls, shape_type: type[S], key_type: type[DK] = str) -> ShapesDictRef[DK, S]:  # type: ignore[assignment]
        """Declare a mapping slot whose values are ``shape_type`` shapes.

        Args:
            shape_type: the Shape class each value holds.
            key_type: the Python type of the keys. Defaults to ``str``.

        Notes:
            - ``users: ShapesDictRef[str, User]`` as an annotation declares
              the same slot.

        Example:
            class Team(Shape):
                users = ShapesDictRef.slot(User)
        """
        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ShapesDictRef[K, S]``."""
        key_type, shape_type = args
        return {
            "shape_type": shape_type,
            "key_type": key_type,
            "key_value_type": value_type_for(key_type),
        }
