"""Dict shapes dict reference — mapping of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_term,
)
from everyshape import Slot
from everyshape.refs import ShapesDictRefBase

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from typing import Self

    from everyabc import Sentinel, Term, Value
    from everyshape import Shape


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type[Value]] = {
        int: IntValue,
        str: StrValue,
        float: FloatValue,
        bool: BoolValue,
        bytes: BytesValue,
        list: ListValue,
        dict: DictValue,
        set: SetValue,
    }
    return mapping.get(python_type, AnyValue)


__all__ = [
    "ShapesDictRef",
]


class ShapesDictRef[K, T: Shape](
    ShapesDictRefBase[K, T],
    RefBase[dict[K, dict]],
):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        key_type: type[K],
        key_value_type: type,
        shape_type: type[T],
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shapes dict reference."""
        super().__init__(address, parent, owner_shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(cls, shape_type: type[T], key_type: type[K] = str) -> Self:  # type: ignore[assignment]
        """Create a slot for this shapes dict ref type.

        Args:
            shape_type: Shape class for values.
            key_type: Python type for keys (default: str).

        Returns:
            Slot that creates ShapesDictRef instances.
        """
        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
        )  # type: ignore[return-value]
