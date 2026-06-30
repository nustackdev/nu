"""virtuals item commands — unsafe primitive write/delete + container materialization.

EnsureLayoutCmd: Materialize view container layout (idempotent setup).
InitItemCmd: Materialize container chain via fetch().
ItemPrimitiveSetUnsafeCmd: Write — _unsafe_primitive_write(ensure_exists=True).
ItemPrimitiveSetUnsafeParentSkipCmd: Write — _unsafe_primitive_write() (full skip).
ItemPrimitiveDeleteUnsafeCmd: Delete — _unsafe_primitive_delete().
ItemPrimitiveStoreCmd: Store value via _primitive_write() — bypasses container type check.

All named explicitly Unsafe — these are optimization internals for tree
deformers, not user-facing APIs. They require virtuals views with
UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from nu import Nu


__all__ = [
    "EnsureLayoutCmd",
    "InitItemCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveStoreCmd",
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
        """Run synchronously."""
        view = self.ref.fetch(ctx)
        if hasattr(view, "_ensure_layout"):
            view._ensure_layout()
        elif hasattr(view, "ensure_created"):
            view.ensure_created()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
        view = await self.ref.afetch(ctx)
        if hasattr(view, "_ensure_layout"):
            view._ensure_layout()
        elif hasattr(view, "ensure_created"):
            view.ensure_created()

    def __repr__(self) -> str:
        return f"EnsureLayoutCmd({self.ref!r})"


class InitItemCmd(ScalarCommand):
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
        """Run synchronously."""
        self.ref.fetch(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
        await self.ref.afetch(ctx)

    def __repr__(self) -> str:
        return f"InitItemCmd({self.ref!r})"


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
        """Run synchronously."""
        from nu import runtime

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = runtime.first(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value, ensure_exists=True)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
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
    The caller must guarantee the container chain exists (e.g. via InitItemCmd).

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
        """Run synchronously."""
        from nu import runtime

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        value = runtime.first(self.value_expr, ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent._unsafe_primitive_write(address, value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
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
        """Run synchronously."""
        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        parent._unsafe_primitive_delete(address)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        parent._unsafe_primitive_delete(address)

    def __repr__(self) -> str:
        return f"ItemPrimitiveDeleteUnsafeCmd({self.ref!r})"


class ItemPrimitiveStoreCmd(ScalarCommand):
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
        """Run synchronously."""
        from nu import runtime

        data = runtime.first(self.data_expr, ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = self.ref.fetch_parent(ctx)
        address = self.ref.resolve_address(ctx)
        parent._primitive_write(address, data)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        """Run."""
        from nu import runtime

        data = await runtime.afirst(self.data_expr, ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")

        parent = await self.ref.afetch_parent(ctx)
        address = await self.ref.aresolve_address(ctx)
        parent._primitive_write(address, data)

    def __repr__(self) -> str:
        return f"ItemPrimitiveStoreCmd({self.ref!r}, {self.data_expr!r})"
