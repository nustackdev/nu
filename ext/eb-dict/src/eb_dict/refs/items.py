# ruff: noqa: D102
"""Dict substrate item refs — typed value holders in nested dicts.

ItemRef combines MutableItemRef (everyshape CRUD) with RefBase
(dict navigation).

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from everybase import Value
from everybase.abc import (
    BoolType,
    BoolValue,
    BytesType,
    BytesValue,
    FloatType,
    FloatValue,
    IntType,
    IntValue,
    StrType,
    StrValue,
)
from everybase.shape import MutableItemRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from everybase import Term
    from everybase.shape import Shape


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef[T, ValueT: Value](
    MutableItemRef[T, ValueT],
    RefBase[T],
):
    """Dict item reference for values in nested dicts."""

    def __init__(
        self,
        *,
        value_type: type[T],
        value_value_type: type[ValueT],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._value_type = value_type
        self._value_value_type = value_value_type

    @classmethod
    def slot(cls, value_type: type[T], value_value_type: type[ValueT]) -> Self:
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with everybase interface)
# =============================================================================


class IntRef(ItemRef[int, IntValue], IntType):
    """Dict integer reference with full numeric interface."""

    def __init__(
        self,
        *,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrValue], StrType):
    """Dict string reference with full string interface."""

    def __init__(
        self,
        *,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatValue], FloatType):
    """Dict float reference with full numeric interface."""

    def __init__(
        self,
        *,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolValue], BoolType):
    """Dict boolean reference with full logical interface."""

    def __init__(
        self,
        *,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=bool,
            value_value_type=BoolValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesValue], BytesType):
    """Dict bytes reference with full bytes interface."""

    def __init__(
        self,
        *,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=bytes,
            value_value_type=BytesValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]
