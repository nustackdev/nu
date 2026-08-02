"""Dict substrate item refs — typed value holders in nested dicts.

``ItemRef`` combines the shape ``MutableItemRef`` blueprint (slot-level CRUD)
with ``RefBase`` (dict navigation). Typed refs (``IntRef``, ``StrRef``, ...) add
the matching primitive Form so the value carries its full operator interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from nu import Bool, Bytes, Float, Int, None_, Str
from nu.domains.shape import MutableItemRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef(MutableItemRef, RefBase):
    """Dict item reference for values in nested dicts."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        value_type: type,
        value_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["value_type"] = value_type
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot(cls, value_type: type, value_value_type: type) -> Self:
        """Declare a generic item slot for ``value_type`` (with its Form)."""
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, Int):
    """Dict integer reference with full numeric interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=int,
            value_value_type=Int,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    def inc(self, step: int | Nu = 1) -> None_:
        """Increment in place."""
        return self.set(self + step)

    def dec(self, step: int | Nu = 1) -> None_:
        """Decrement in place."""
        return self.set(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef, Str):
    """Dict string reference with full string interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef, Float):
    """Dict float reference with full numeric interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=Float,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef, Bool):
    """Dict boolean reference with full logical interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bool,
            value_value_type=Bool,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef, Bytes):
    """Dict bytes reference with full bytes interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bytes,
            value_value_type=Bytes,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]
