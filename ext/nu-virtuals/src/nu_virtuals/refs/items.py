"""Concrete PV item ref implementations.

Item refs combine ReactiveItemRef (everyshape document model) with
PrimitiveRef (PV substrate) for CRUD + observation on PV storage.

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.

Pattern:
    class ItemRef(ReactiveItemRef[T, ValueT], PrimitiveRef[T]):
        # Document model (CRUD + observe) + PV substrate

    class IntRef(ItemRef[int, IntForm], IntForm):
        # PV item + int operators
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from nu import (
    BoolForm,
    BytesForm,
    DictForm,
    FloatForm,
    IntForm,
    ListForm,
    NoneForm,
    SetForm,
    StrForm,
)
from nu.shapes import ReactiveItemRef, Slot
from nu.terms import Mode

from .base import PrimitiveRef


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context


if TYPE_CHECKING:
    from nu import Form, Nu
    from nu.shapes import Shape
    from virtuals.loc import path

__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "PrimitiveDictRef",
    "PrimitiveListRef",
    "PrimitiveSetRef",
    "StrRef",
]


# =============================================================================
# ITEM REFS (document model + PV substrate)
# =============================================================================


class ItemRef[T, ValueT: Form](
    ReactiveItemRef[T, ValueT],
    PrimitiveRef[T],
):
    """PV item reference for primitive values.

    Combines everyshape document model (CRUD + observation) with
    PV substrate (path resolution, view navigation).

    Uses the base ReactiveItemRef.store(), which emits ItemStoreCmd and
    routes through the parent view's __setitem__. This respects view-specific
    semantics (e.g. LogIndexedDictView's __data__ + __keys__ layout).
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        value_value_type: type[ValueT],
        **kwargs: object,
    ) -> None:
        """Initialize item reference."""
        super().__init__(**kwargs)
        self._value_value_type = value_value_type

    @classmethod
    def slot(
        cls,
        value_type: type[T],
        value_value_type: type[ValueT],
    ) -> Self:
        """Create a slot for this item ref type.

        Args:
            value_type: Python type of the value (int, str, float, etc.)
            value_value_type: Value type for serialization

        Returns:
            Slot configured to create ItemRef instances
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore


# =============================================================================
# TYPED REFS (with everybase interface)
# =============================================================================


class IntRef(ItemRef[int, IntForm], IntForm):
    """PV integer reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - IntForm: Arithmetic, comparison, bitwise, logical operators
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    def inc(self, step: int | Nu = 1) -> NoneForm:
        """Increment in place."""
        return self.store(self + step)

    def dec(self, step: int | Nu = 1) -> NoneForm:
        """Decrement in place."""
        return self.store(self - step)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for int values."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrForm], StrForm):
    """PV string reference with full string interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - StrForm: String methods (upper, lower, split, etc.), concatenation
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for str values."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatForm], FloatForm):
    """PV float reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - FloatForm: Arithmetic, comparison, logical operators
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for float values."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolForm], BoolForm):
    """PV boolean reference with full logical interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BoolForm: Logical operators (and_, or_, not_)
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(
            address=address,
            value_type=bool,
            value_value_type=BoolForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bool values."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesForm], BytesForm):
    """PV bytes reference with full bytes interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BytesForm: Bytes methods (decode, hex, etc.)
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(
            address=address,
            value_type=bytes,
            value_value_type=BytesForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bytes values."""
        return Slot(cls)  # type: ignore[return-value]


# =============================================================================
# COMPOUND PRIMITIVE REFS (stored as single blob, not decomposed)
# =============================================================================


class PrimitiveDictRef[K, V](
    ItemRef[dict[K, V], DictForm[K, V]],
    DictForm[K, V],
):
    """PV dict reference stored as a single primitive blob.

    Unlike DictRef which decomposes into per-key storage, this stores the
    entire dict as one value. Operations work on the fetched Python dict.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - DictForm: Dict methods (keys, values, items, get, set, etc.)
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive dict ref."""
        super().__init__(
            address=address,
            value_type=dict,
            value_value_type=DictForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive dict values."""
        return Slot(cls)  # type: ignore[return-value]

    # TODO task-079: write-back view (Stream D). Yields mutable view, flushes
    # on generator close. Override `aopen` directly so finally runs on aclose.
    async def aopen(self, ctx: Context) -> AsyncGenerator[object, None]:
        """Yield a write-back dict view; flush on generator close if dirty."""
        from nu_virtuals.views import PrimitiveDictView

        parent = await self.afetch_parent(ctx)
        address = await self.aresolve_address(ctx)
        try:
            current = parent[address]
        except (KeyError, IndexError):
            current = {}
        view = PrimitiveDictView(current, parent=parent, address=address)
        try:
            yield view
        finally:
            view._flush()


class PrimitiveListRef[T](
    ItemRef[list[T], ListForm[T]],
    ListForm[T],
):
    """PV list reference stored as a single primitive blob.

    Unlike ListRef which decomposes into per-index storage, this stores the
    entire list as one value. Operations work on the fetched Python list.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - ListForm: List methods (append, extend, insert, etc.)
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive list ref."""
        super().__init__(
            address=address,
            value_type=list,
            value_value_type=ListForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive list values."""
        return Slot(cls)  # type: ignore[return-value]

    # TODO task-079: write-back view (Stream D). Yields mutable view, flushes
    # on generator close. Override `aopen` directly so finally runs on aclose.
    async def aopen(self, ctx: Context) -> AsyncGenerator[object, None]:
        """Yield a write-back list view; flush on generator close if dirty."""
        from nu_virtuals.views import PrimitiveListView

        parent = await self.afetch_parent(ctx)
        address = await self.aresolve_address(ctx)
        try:
            current = parent[address]
        except (KeyError, IndexError):
            current = []
        view = PrimitiveListView(current, parent=parent, address=address)
        try:
            yield view
        finally:
            view._flush()


class PrimitiveSetRef[T](
    ItemRef[set[T], SetForm[T]],
    SetForm[T],
):
    """PV set reference stored as a single primitive blob.

    Unlike SetRef which decomposes into per-element storage, this stores the
    entire set as one value. Operations work on the fetched Python set.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - SetForm: Set methods (add, remove, union, intersection, etc.)
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive set ref."""
        super().__init__(
            address=address,
            value_type=set,
            value_value_type=SetForm,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive set values."""
        return Slot(cls)  # type: ignore[return-value]

    # TODO task-079: write-back view (Stream D). Yields mutable view, flushes
    # on generator close. Override `aopen` directly so finally runs on aclose.
    async def aopen(self, ctx: Context) -> AsyncGenerator[object, None]:
        """Yield a write-back set view; flush on generator close if dirty."""
        from nu_virtuals.views import PrimitiveSetView

        parent = await self.afetch_parent(ctx)
        address = await self.aresolve_address(ctx)
        try:
            current = parent[address]
        except (KeyError, IndexError):
            current = set()
        view = PrimitiveSetView(current, parent=parent, address=address)
        try:
            yield view
        finally:
            view._flush()
