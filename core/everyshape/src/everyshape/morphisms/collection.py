# ruff: noqa: D102
"""Collection-level morphisms — extract, store, length, clear, existence.

ExtractOp: Read entire collection as Python value — ref.fetch(ctx).extract()
StoreCmd: Replace collection contents — ref.fetch(ctx).store(data)
CollectionLenOp: Get collection length — len(ref.fetch(ctx))
CollectionClearCmd: Clear all items — ref.fetch(ctx).clear()
CollectionExistsOp: Check if collection exists — try fetch, catch errors
CollectionMissingOp: Inverse of CollectionExistsOp

These operate on refs that implement fetch(ctx) -> storage object.
The storage object must support the relevant protocol (extract(), store(),
__len__, clear()).

PV-specific collection morphisms (ScanPrimitivesOp, ClearPrimitivesCmd)
live in everypv.morphisms.collection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import EMPTY, Command, Morphism, Operation, Sentinel
from everyshape.protocols import ClearableProtocol, ExtractableProtocol, StorableProtocol


if TYPE_CHECKING:
    from everybase import Context, Term


__all__ = [
    "CollectionClearCmd",
    "CollectionExistsOp",
    "CollectionMissingOp",
    "ExtractOp",
    "StoreCmd",
]


class ExtractOp[T](Operation, Morphism[T | Sentinel]):
    """Extract entire collection as a Python value.

    Calls extract() on the storage object (Convertible protocol).

    The ref must implement:
        fetch(ctx) -> storage object with extract() method
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        try:
            view = await self.ref.fetch(ctx)
        except (KeyError, IndexError):
            return EMPTY

        if not isinstance(view, ExtractableProtocol):
            raise TypeError(f"{type(view).__name__} does not support extract()")
        return view.extract()

    def __repr__(self) -> str:
        return f"ExtractOp({self.ref!r})"


class StoreCmd[T](Command, Morphism[T]):
    """Replace collection contents from a Python value.

    Calls store(data) on the storage object (Initializable protocol).

    The ref must implement:
        fetch(ctx) -> storage object with store() method
    """

    def __init__(self, ref: object, data: Term[T | Sentinel]) -> None:
        super().__init__(ref, data)
        self.ref = ref
        self.data_expr = data

    async def execute(self, ctx: Context) -> T:
        data = await self.data_expr.execute(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")

        view = await self.ref.fetch(ctx)

        if not isinstance(view, StorableProtocol):
            raise TypeError(f"{type(view).__name__} does not support store()")
        view.store(data)
        return data

    def __repr__(self) -> str:
        return f"StoreCmd({self.ref!r}, {self.data_expr!r})"


class CollectionClearCmd(Command, Morphism[None]):
    """Clear all items from collection: view.clear().

    The ref must implement:
        fetch(ctx) -> storage object with clear() method
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        view = await self.ref.fetch(ctx)
        if not isinstance(view, ClearableProtocol):
            raise TypeError(f"{type(view).__name__} does not support clear()")
        view.clear()
        return None

    def __repr__(self) -> str:
        return f"CollectionClearCmd({self.ref!r})"


class CollectionExistsOp(Operation, Morphism[bool]):
    """Check if collection/view exists.

    Tries to fetch the storage object. Returns True if successful,
    False if KeyError/IndexError.

    The ref must implement:
        fetch(ctx) -> storage object
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        try:
            await self.ref.fetch(ctx)
            return True
        except (KeyError, IndexError):
            return False

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self.ref!r})"


class CollectionMissingOp(Operation, Morphism[bool]):
    """Check if collection/view is missing. Inverse of CollectionExistsOp."""

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        try:
            await self.ref.fetch(ctx)
            return False
        except (KeyError, IndexError):
            return True

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self.ref!r})"
