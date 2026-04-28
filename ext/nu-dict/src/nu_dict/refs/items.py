# ruff: noqa: D102
"""Dict substrate item refs — typed value holders in nested dicts.

ItemRef combines MutableItemRef (everyshape CRUD) with RefBase
(dict navigation).

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from nu import (
    BoolI,
    BytesI,
    FloatI,
    Interface,
    IntI,
    NoneI,
    StrI,
)
from nu.shapes import MutableItemRef, Slot
from nu.terms import Mode

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu
    from nu.shapes import Shape


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef[T, ValueT: Interface](
    MutableItemRef[T, ValueT],
    RefBase[T],
):
    """Dict item reference for values in nested dicts."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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


class IntRef(ItemRef[int, IntI], IntI):
    """Dict integer reference with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntI,
            parent=parent,
            owner_shape=owner_shape,
        )

    def inc(self, step: int | Nu = 1) -> NoneI:
        """Increment in place."""
        return self.store(self + step)

    def dec(self, step: int | Nu = 1) -> NoneI:
        """Decrement in place."""
        return self.store(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrI], StrI):
    """Dict string reference with full string interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatI], FloatI):
    """Dict float reference with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolI], BoolI):
    """Dict boolean reference with full logical interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=bool,
            value_value_type=BoolI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesI], BytesI):
    """Dict bytes reference with full bytes interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | int | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=bytes,
            value_value_type=BytesI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        return Slot(cls)  # type: ignore[return-value]
