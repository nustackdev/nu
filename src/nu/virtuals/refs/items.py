"""Virtuals item refs — typed leaf-value holders backed by virtuals storage.

``ItemRef`` combines the shape ``ReactiveItemRef`` blueprint (slot-level CRUD +
change observation) with ``PrimitiveRef`` (virtuals leaf navigation). Typed
refs (``IntRef``, ``StrRef``, ...) add the matching primitive Form so the value
carries its full operator interface.

Reactivity is uniform: ``ReactiveItemForm.on_change()`` -> ``nu.core.reactive
.OnPrimitiveChangeQuery`` calls ``ref._afetch_parent`` + ``ref._aaddress`` on the
leaf, and the virtuals ``PrimitiveRef`` implements both -- no substrate-side
override needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from nu import BoolForm, BytesForm, FloatForm, IntForm, NoneForm, StrForm
from nu.domains.shape import ReactiveItemRef, Slot

from .base import PrimitiveRef


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


class ItemRef(ReactiveItemRef, PrimitiveRef):
    """Virtuals item reference for primitive leaf values."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        value_type: type,
        value_value_type: type,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, value_type=value_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot(cls, value_type: type, value_value_type: type) -> Self:
        """Declare a generic item slot for ``value_type`` (with its Form)."""
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with primitive Form interface)
# =============================================================================


class IntRef(ItemRef, IntForm):
    """Virtuals integer reference with full numeric interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=int,
            value_value_type=IntForm,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    def inc(self, step: int | Nu = 1) -> NoneForm:
        """Increment in place."""
        return self.set(self + step)

    def dec(self, step: int | Nu = 1) -> NoneForm:
        """Decrement in place."""
        return self.set(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef, StrForm):
    """Virtuals string reference with full string interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=StrForm,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef, FloatForm):
    """Virtuals float reference with full numeric interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=FloatForm,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef, BoolForm):
    """Virtuals boolean reference with full logical interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bool,
            value_value_type=BoolForm,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef, BytesForm):
    """Virtuals bytes reference with full bytes interface."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=bytes,
            value_value_type=BytesForm,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding this typed value."""
        return Slot(cls)  # type: ignore[return-value]
