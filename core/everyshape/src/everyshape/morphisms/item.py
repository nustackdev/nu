# ruff: noqa: D102
"""Item access morphisms — CRUD for items within collections.

ItemGetOp: Read item value — parent[address]
ItemSetCmd: Write item value — parent[address] = value
ItemDeleteCmd: Delete item — del parent[address]
ItemExistsOp: Check if item exists — address in parent
ItemMissingOp: Check if item is missing — address not in parent

These operate via standard Python protocols (__getitem__, __setitem__,
__delitem__, __contains__). The ref provides fetch_parent(ctx) to get
the collection and resolve_address(ctx) to get the key/index.

Any substrate ref that implements fetch_parent(ctx) and resolve_address(ctx)
can use these morphisms directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import EMPTY, Command, Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from everybase import Context, Term


__all__ = [
    "InitCmd",
    "ItemDeleteCmd",
    "ItemExistsOp",
    "ItemGetOp",
    "ItemMissingOp",
    "ItemPrimitiveSetCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemSetCmd",
]


class InitCmd(Command, Morphism[None]):
    """Materialize container chain for a ViewRef.

    Navigates the view hierarchy via fetch(), triggering ensure_created()
    along the way. This guarantees all parent containers exist in storage,
    allowing subsequent unsafe writes to skip validation reads.

    The ref must implement:
        fetch(ctx) -> view object
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        # fetch() navigates the view hierarchy, triggering ensure_created() along the way
        await self.ref.fetch(ctx)
        return None

    def __repr__(self) -> str:
        return f"InitCmd({self.ref!r})"


class ItemGetOp[T](Operation, Morphism[T | Sentinel]):
    """Read item from collection: parent[address].

    Uses __getitem__ on the parent collection. Returns EMPTY
    if the key/index doesn't exist.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        try:
            return parent[address]
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"ItemGetOp({self.ref!r})"


class ItemSetCmd[T](Command, Morphism[T]):
    """Write item to collection: parent[address] = value.

    Uses __setitem__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> T:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value
        return value

    def __repr__(self) -> str:
        return f"ItemSetCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveSetCmd[T](Command, Morphism[T]):
    """Set primitive value via _set_primitive() on the parent view.

    Uses the ChildPrimitiveSetBase._set_primitive() method which
    materializes containers and writes with full validation.

    The ref must implement:
        fetch_parent(ctx) -> view with _set_primitive()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> T:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._set_primitive(address, value)
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveSetUnsafeCmd[T](Command, Morphism[T]):
    """Set primitive value skipping validation reads.

    Uses the ChildPrimitiveUnsafeSetBase._set_primitive_unsafe() method
    which materializes containers but skips the 2 validation storage reads
    (validate_is_container on parent + get_node_info on child).

    The ref must implement:
        fetch_parent(ctx) -> view with _set_primitive_unsafe()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> T:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._set_primitive_unsafe(address, value)
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetUnsafeCmd({self.ref!r}, {self.value_expr!r})"


class ItemDeleteCmd(Command, Morphism[None]):
    """Delete item from collection: del parent[address].

    Uses __delitem__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        del parent[address]
        return None

    def __repr__(self) -> str:
        return f"ItemDeleteCmd({self.ref!r})"


class ItemExistsOp(Operation, Morphism[bool]):
    """Check if item exists in collection: address in parent.

    Uses __contains__ on the parent collection.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address in parent

    def __repr__(self) -> str:
        return f"ItemExistsOp({self.ref!r})"


class ItemMissingOp(Operation, Morphism[bool]):
    """Check if item is missing from collection: address not in parent.

    Inverse of ItemExistsOp.

    The ref must implement:
        fetch_parent(ctx) -> collection object
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> bool:
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        return address not in parent

    def __repr__(self) -> str:
        return f"ItemMissingOp({self.ref!r})"
