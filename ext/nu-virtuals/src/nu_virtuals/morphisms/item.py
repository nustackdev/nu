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

from nu import EMPTY, Command, Op, Calculation, Sentinel


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = [
    "EnsureLayoutCmd",
    "InitCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "PrimitiveStoreCmd",
]


class EnsureLayoutCmd(Command, Op[None]):
    """Ensure view container and its internal layout exist in storage.

    Navigates to the view via fetch(), then calls _ensure_layout() to
    create internal containers (__keys__, __data__, etc.). For views
    without _ensure_layout, falls back to ensure_created().

    Use before distributed workers start to avoid concurrent layout
    creation (lock contention on shared DB).

    The ref must implement:
        fetch(ctx) -> view object
    """

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        view = await self.ref.fetch(ctx)
        if hasattr(view, "_ensure_layout"):
            view._ensure_layout()
        elif hasattr(view, "ensure_created"):
            view.ensure_created()
        return None

    def __repr__(self) -> str:
        return f"EnsureLayoutCmd({self.ref!r})"


class InitCmd(Command, Op[None]):
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


class ItemPrimitiveGetUnsafeOp[T](Calculation, Op[T | Sentinel]):
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


class ItemPrimitiveSetUnsafeCmd[T](Command, Op[T]):
    """Write primitive via _unsafe_primitive_write(ensure_exists=True).

    Ensures the container chain exists before writing (calls ensure_created),
    but skips child type validation. Less dangerous than ParentSkip variant.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Nu[T | Sentinel]) -> None:
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


class ItemPrimitiveSetUnsafeParentSkipCmd[T](Command, Op[T]):
    """Write primitive via _unsafe_primitive_write() — full skip.

    Single ctx.put() call — no ensure_created, no validation reads.
    The caller must guarantee the container chain exists (e.g. via InitCmd).

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, value: Nu[T | Sentinel]) -> None:
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


class ItemPrimitiveDeleteUnsafeCmd(Command, Op[None]):
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


class PrimitiveStoreCmd[T](Command, Op[None]):
    """Store a value via _primitive_write(), bypassing container type checks.

    Uses PrimitiveOpsBase._primitive_write() which does ensure_created() +
    direct ctx.put(). Skips the is_container_type check that __setitem__
    would trigger, avoiding unnecessary overhead for primitives and preventing
    decomposition for compound values stored as blobs.

    The ref must implement:
        fetch_parent(ctx) -> view with PrimitiveOpsBase._primitive_write()
        resolve_address(ctx) -> key/index
    """

    def __init__(self, ref: object, data: object) -> None:
        super().__init__(ref, data)
        self.ref = ref
        self.data_expr = data

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        data = await self.data_expr.execute(ctx)
        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = await self.ref.fetch_parent(ctx)
        address = await self.ref.resolve_address(ctx)
        parent._primitive_write(address, data)
        return None

    def __repr__(self) -> str:
        return f"PrimitiveStoreCmd({self.ref!r}, {self.data_expr!r})"
