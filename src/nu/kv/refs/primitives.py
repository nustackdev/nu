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
    from nu.lang import Arg, IntArg, StrArg

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
    """A list leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Stored as one opaque value, so the elements get no addresses of
          their own and cannot be reached or watched individually.
        - Reads come back as a real Python list, so heterogeneous and nested
          contents round-trip as they were written.
        - The write path is ``set`` with a whole list. The element-level
          mutations inherited from the List surface (``append``, ``insert``,
          ``del_at``, ...) do not reach the stored blob and leave it as it
          was, without raising.
        - ListRef is the other choice: it decomposes into per-index storage
          and gives per-element navigation.

    Example:
        class Bag(Shape):
            rows = PrimitiveListRef.slot()
        run(Bag.rows.set([1, "two", {"three": 3}]), ctx)
        run(Bag.rows, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Store the whole list as one leaf value.

        Args:
            value: the list to store. May be a literal or an expression.

        Notes:
            - Overrides the decomposing slot write, so the list lands as one
              opaque value with no per-index children underneath it.
            - Replaces whatever was there; there is no merge with the value
              already stored.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.rows.set([1, "two"]), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveDictRef(ItemRef, Dict[K, V], Generic[K, V]):
    """A dict leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Stored as one opaque value, so the keys get no addresses of their
          own and cannot be reached or watched individually.
        - Reads come back as a real Python dict, nested contents included.
        - The write path is ``set`` with a whole dict. The key-level
          mutations inherited from the Dict surface (``set_item``, ``pop``,
          ``update``, ...) do not reach the stored blob and leave it as it
          was, without raising.
        - DictRef is the other choice: it decomposes into per-key storage
          and gives per-key navigation and change observation.

    Example:
        class Bag(Shape):
            meta = PrimitiveDictRef.slot()
        run(Bag.meta.set({"a": 1, "b": [2, 3]}), ctx)
        run(Bag.meta, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Store the whole dict as one leaf value.

        Args:
            value: the dict to store. May be a literal or an expression.

        Notes:
            - Overrides the decomposing slot write, so the dict lands as one
              opaque value with no per-key children underneath it.
            - Replaces whatever was there; keys already stored are not
              merged in.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.meta.set({"a": 1}), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveTupleRef(ItemRef, Tuple):
    """A tuple leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python tuple, so the type survives the
          round trip rather than degrading to a list.
        - Has no decomposing counterpart: a tuple slot is always stored
          whole.
        - Elements get no addresses of their own, so nothing under it can be
          reached or watched individually.

    Example:
        class Bag(Shape):
            pair = PrimitiveTupleRef.slot()
        run(Bag.pair.set((1, "two")), ctx)
        run(Bag.pair, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Store the whole tuple as one leaf value.

        Args:
            value: the tuple to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.pair.set((1, "two")), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveSetRef(ItemRef, Set[T], Generic[T]):
    """A set leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python set, so membership and the set
          operators work on the value as they would in Python.
        - The write path is ``set`` with a whole set. The element-level
          mutations inherited from the Set surface (``add``, ``discard``,
          ``update``, ...) do not reach the stored blob and leave it as it
          was, without raising.
        - SetRef is the other choice: it decomposes into per-element storage
          and gives change observation.

    Example:
        class Bag(Shape):
            members = PrimitiveSetRef.slot()
        run(Bag.members.set({1, 2, 3}), ctx)
        run(Bag.members, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Store the whole set as one leaf value.

        Args:
            value: the set to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there; it is not a union with the set
              already stored.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.members.set({1, 2}), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveFrozenSetRef(ItemRef, FrozenSet[T], Generic[T]):
    """A frozenset leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python frozenset, so the type survives
          the round trip.
        - Carries the read-only set surface only: union, intersection and
          the rest yield new values and never touch storage.
        - Has no decomposing counterpart; a frozenset slot is always stored
          whole.

    Example:
        class Bag(Shape):
            locked = PrimitiveFrozenSetRef.slot()
        run(Bag.locked.set(frozenset({1, 2})), ctx)
        run(Bag.locked, ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Store the whole frozenset as one leaf value.

        Args:
            value: the frozenset to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.locked.set(frozenset({1, 2})), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)
