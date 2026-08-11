"""virtuals-substrate refs for whole-blob compound values.

Unlike the decomposing container refs (``ListRef`` / ``DictRef`` / ``SetRef``,
which fan a container out into per-element storage), these write the whole
container as one opaque value via ``ItemPrimitiveSetCmd`` and read it back as
a plain Python object. Each mixes in the matching collection Form, so the value
still carries the full list / dict / tuple / set interface.

Use for opaque or heterogeneous containers that should round-trip whole rather
than shape-decompose (log lines, raw account blobs, balance arrays, ...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.forms import Dict, FrozenSet, List, Set, Tuple

from .items import ItemRef


if TYPE_CHECKING:
    from nu.domains.shape import Shape
    from nu.lang import Arg, Nu

    from .base import PrimitiveRef


__all__ = [
    "PrimitiveDictRef",
    "PrimitiveFrozenSetRef",
    "PrimitiveListRef",
    "PrimitiveSetRef",
    "PrimitiveTupleRef",
]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class PrimitiveListRef(ItemRef, List[T], Generic[T]):
    """virtuals list stored as a single primitive blob."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=list,
            value_value_type=List,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a whole-blob primitive list."""
        return Slot(cls)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The elem type is purely for typing; no runtime kwargs needed."""
        return {}

    def _lift(self, raw: object) -> list:
        """Return the stored value as a plain list."""
        return raw if isinstance(raw, list) else list(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[list[T]]) -> object:
        """Write the whole list as one primitive blob (no per-index decomposition)."""
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveDictRef(ItemRef, Dict[K, V], Generic[K, V]):
    """virtuals dict stored as a single primitive blob."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=dict,
            value_value_type=Dict,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a whole-blob primitive dict."""
        return Slot(cls)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The elem type is purely for typing; no runtime kwargs needed."""
        return {}

    def _lift(self, raw: object) -> dict:
        """Return the stored value as a plain dict."""
        return raw if isinstance(raw, dict) else dict(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[dict[K, V]]) -> object:
        """Write the whole dict as one primitive blob (no per-key decomposition)."""
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveTupleRef(ItemRef, Tuple):
    """virtuals tuple stored as a single primitive blob."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=tuple,
            value_value_type=Tuple,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a whole-blob primitive tuple."""
        return Slot(cls)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The elem type is purely for typing; no runtime kwargs needed."""
        return {}

    def _lift(self, raw: object) -> tuple:
        """Return the stored value as a plain tuple."""
        return raw if isinstance(raw, tuple) else tuple(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[tuple]) -> object:
        """Write the whole tuple as one primitive blob."""
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveSetRef(ItemRef, Set[T], Generic[T]):
    """virtuals set stored as a single primitive blob."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=set,
            value_value_type=Set,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a whole-blob primitive set."""
        return Slot(cls)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The elem type is purely for typing; no runtime kwargs needed."""
        return {}

    def _lift(self, raw: object) -> set:
        """Return the stored value as a plain set."""
        return raw if isinstance(raw, set) else set(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[set[T]]) -> object:
        """Write the whole set as one primitive blob."""
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveFrozenSetRef(ItemRef, FrozenSet[T], Generic[T]):
    """virtuals frozenset stored as a single primitive blob."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=frozenset,
            value_value_type=FrozenSet,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a whole-blob primitive frozenset."""
        return Slot(cls)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The elem type is purely for typing; no runtime kwargs needed."""
        return {}

    def _lift(self, raw: object) -> frozenset:
        """Return the stored value as a plain frozenset."""
        return raw if isinstance(raw, frozenset) else frozenset(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[frozenset[T]]) -> object:
        """Write the whole frozenset as one primitive blob."""
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)
