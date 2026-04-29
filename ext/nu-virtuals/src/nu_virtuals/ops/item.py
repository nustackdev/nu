"""PV item ops — unsafe primitive CRUD via UnsafePrimitiveOpsBase.

InitCmd: Materialize container chain — ref.afetch(ctx) triggers ensure_created()
ItemPrimitiveGetUnsafeOp: Read — _unsafe_primitive_read() (single ctx.get)
ItemPrimitiveSetUnsafeCmd: Write — _unsafe_primitive_write(ensure_exists=True)
ItemPrimitiveSetUnsafeParentSkipCmd: Write — _unsafe_primitive_write() (full skip)
ItemPrimitiveDeleteUnsafeCmd: Delete — _unsafe_primitive_delete() (single ctx.delete)

All named explicitly Unsafe — these are optimization internals for tree
deformers, not user-facing APIs.

These require PV views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import EMPTY, is_sentinel
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from nu import Nu


__all__ = [
    "EnsureLayoutCmd",
    "InitCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "PrimitiveStoreCmd",
]


class EnsureLayoutCmd(ScalarCommand):
    """Ensure view container and its internal layout exist in storage.

    Navigates to the view via fetch(), then calls _ensure_layout() to
    create internal containers (__keys__, __data__, etc.). For views
    without _ensure_layout, falls back to ensure_created().

    Use before distributed workers start to avoid concurrent layout
    creation (lock contention on shared DB).

    The ref must implement:
        fetch(ctx) -> view object
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        view = self.ref.fetch(ctx)
        if hasattr(view, "_ensure_layout"):
            view._ensure_layout()
        elif hasattr(view, "ensure_created"):
            view.ensure_created()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        view = await self.ref.afetch(ctx)
        if hasattr(view, "_ensure_layout"):
            view._ensure_layout()
        elif hasattr(view, "ensure_created"):
            view.ensure_created()

    def __repr__(self) -> str:
        return f"EnsureLayoutCmd({self.ref!r})"


class InitCmd(ScalarCommand):
    """Materialize container chain for a ViewRef.

    Navigates the view hierarchy via fetch(), triggering ensure_created()
    along the way. This guarantees all parent containers exist in storage,
    allowing subsequent unsafe writes to skip validation reads.

    The ref must implement:
        fetch(ctx) -> view object
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        """Fetch view hierarchy, materializing containers along the way (sync)."""
        self.ref.fetch(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Fetch view hierarchy, materializing containers along the way."""
        await self.ref.afetch(ctx)

    def __repr__(self) -> str:
        return f"InitCmd({self.ref!r})"


class ItemPrimitiveGetUnsafeOp(ScalarQuery):
    """Read primitive value via _unsafe_primitive_read().

    Single ctx[] call — no marker parsing, no type checks.
    Returns EMPTY if the value doesn't exist.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_read()
        resolve_address(ctx) -> key/index
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        """Read primitive via single ctx[] lookup (sync)."""
        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = parent._unsafe_primitive_read(address)
        if is_sentinel(value):
            return EMPTY
        return value

    async def _aapply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        """Read primitive via single ctx[] lookup."""
        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        value = parent._unsafe_primitive_read(address)
        if is_sentinel(value):
            return EMPTY
        return value

    def __repr__(self) -> str:
        return f"ItemPrimitiveGetUnsafeOp({self.ref!r})"


class ItemPrimitiveSetUnsafeCmd(ScalarCommand):
    """Write primitive via _unsafe_primitive_write(ensure_exists=True).

    Ensures the container chain exists before writing (calls ensure_created),
    but skips child type validation. Less dangerous than ParentSkip variant.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object, value: Nu) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        """Write primitive via ctx.put() with ensure_exists (sync)."""
        from nu import runtime

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = runtime.first(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value, ensure_exists=True)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Write primitive via ctx.put() with ensure_exists."""
        from nu import runtime

        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        value = await runtime.afirst(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value, ensure_exists=True)

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetUnsafeCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveSetUnsafeParentSkipCmd(ScalarCommand):
    """Write primitive via _unsafe_primitive_write() -- full skip.

    Single ctx.put() call -- no ensure_created, no validation reads.
    The caller must guarantee the container chain exists (e.g. via InitCmd).

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_write()
        resolve_address(ctx) -> key/index
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object, value: Nu) -> None:
        super().__init__(ref, value)
        self.ref = ref
        self.value_expr = value

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        """Write primitive via single ctx.put(), skipping all validation (sync)."""
        from nu import runtime

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = runtime.first(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Write primitive via single ctx.put(), skipping all validation."""
        from nu import runtime

        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        value = await runtime.afirst(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value)

    def __repr__(self) -> str:
        return f"ItemPrimitiveSetUnsafeParentSkipCmd({self.ref!r}, {self.value_expr!r})"


class ItemPrimitiveDeleteUnsafeCmd(ScalarCommand):
    """Delete primitive via _unsafe_primitive_delete().

    Single ctx.delete() call -- no validation, no descendant cleanup.
    The caller must know the child is a primitive.

    The ref must implement:
        fetch_parent(ctx) -> view with _unsafe_primitive_delete()
        resolve_address(ctx) -> key/index
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        """Delete primitive via single ctx.delete() (sync)."""
        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        parent._unsafe_primitive_delete(address)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Delete primitive via single ctx.delete()."""
        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        parent._unsafe_primitive_delete(address)

    def __repr__(self) -> str:
        return f"ItemPrimitiveDeleteUnsafeCmd({self.ref!r})"


class PrimitiveStoreCmd(ScalarCommand):
    """Store a value via _primitive_write(), bypassing container type checks.

    Uses PrimitiveOpsBase._primitive_write() which does ensure_created() +
    direct ctx.put(). Skips the is_container_type check that __setitem__
    would trigger, avoiding unnecessary overhead for primitives and preventing
    decomposition for compound values stored as blobs.

    The ref must implement:
        fetch_parent(ctx) -> view with PrimitiveOpsBase._primitive_write()
        resolve_address(ctx) -> key/index
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object, data: object) -> None:
        super().__init__(ref, data)
        self.ref = ref
        self.data_expr = data

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        data = runtime.first(self.data_expr, ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        parent._primitive_write(address, data)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        data = await runtime.afirst(self.data_expr, ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        parent._primitive_write(address, data)

    def __repr__(self) -> str:
        return f"PrimitiveStoreCmd({self.ref!r}, {self.data_expr!r})"
