"""PV item morphisms — unsafe primitive CRUD via UnsafePrimitiveOpsBase.

InitCmd: Materialize container chain — ref.fetch(ctx) triggers ensure_created()
ItemPrimitiveGetUnsafeOp: Read — _unsafe_primitive_read() (single ctx.get)
ItemPrimitiveSetUnsafeCmd: Write — _unsafe_primitive_write(ensure_exists=True)
ItemPrimitiveSetUnsafeParentSkipCmd: Write — _unsafe_primitive_write() (full skip)
ItemPrimitiveDeleteUnsafeCmd: Delete — _unsafe_primitive_delete() (single ctx.delete)

All named explicitly Unsafe — these are optimization internals for tree
deformers, not user-facing APIs.

These require PV views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import EMPTY, Command, Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from everybase import Context, Term


__all__ = [
    "InitCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
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
        """Fetch view hierarchy, materializing containers along the way."""
        await self.ref.fetch(ctx)
        return None

    def __repr__(self) -> str:
        return f"InitCmd({self.ref!r})"


class ItemPrimitiveGetUnsafeOp[T](Operation, Morphism[T | Sentinel]):
    """Read primitive value via _unsafe_primitive_read().

    Single ctx[] call — no marker parsing, no type checks.
    Returns EMPTY if the value doesn't exist.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_read()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Read primitive via single ctx[] lookup."""
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = parent._unsafe_primitive_read(address)
        if isinstance(value, Sentinel):
            return EMPTY
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveGetUnsafeOp({self.ref!r})"


class ItemPrimitiveSetUnsafeCmd[T](Command, Morphism[T]):
    """Write primitive via _unsafe_primitive_write(ensure_exists=True).

    Ensures the container chain exists before writing (calls ensure_created),
    but skips child type validation. Less dangerous than ParentSkip variant.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> T:
        """Write primitive via ctx.put() with ensure_exists."""
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value, ensure_exists=True)
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetUnsafeCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveSetUnsafeParentSkipCmd[T](Command, Morphism[T]):
    """Write primitive via _unsafe_primitive_write() — full skip.

    Single ctx.put() call — no ensure_created, no validation reads.
    The caller must guarantee the container chain exists (e.g. via InitCmd).

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Term[T | Sentinel]) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    async def execute(self, ctx: Context) -> T:
        """Write primitive via single ctx.put(), skipping all validation."""
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        value = await self.value_expr.execute(ctx)
        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value)
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetUnsafeParentSkipCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveDeleteUnsafeCmd(Command, Morphism[None]):
    """Delete primitive via _unsafe_primitive_delete().

    Single ctx.delete() call — no validation, no descendant cleanup.
    The caller must know the child is a primitive.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_delete()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:
        """Delete primitive via single ctx.delete()."""
        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        parent._unsafe_primitive_delete(address)
        return None

    def __repr__(self) -> str:
        return f"ItemPrimitiveDeleteUnsafeCmd({self.ref!r})"
