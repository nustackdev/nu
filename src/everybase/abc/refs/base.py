"""PrimRef — flat name-based lookup from Context."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import Ref, Sentinel


if TYPE_CHECKING:
    from everybase.core import Value

    from ..values import BoolValue

__all__ = [
    "PrimRef",
]


class PrimRef[T](Ref[T]):
    """Primitive ref — flat name-based lookup from Context.

    The simplest substrate: resolves a name directly from ctx.
    No parent chain, no shape, no hierarchical addressing.

    Usage:
        ref = PrimRef("error")
        val = await ref.fetch(ctx)  # → ctx["error"]
    """

    value_type: type = object

    def __init__(self, name: str) -> None:
        """Initialize with name tag."""
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        """The name tag for context lookup."""
        return self._name

    async def resolve(self, ctx: object) -> str:
        """Resolve to the name string."""
        return self._name

    async def fetch(self, ctx: object) -> T | Sentinel:
        """Fetch value from context attrs by name."""
        return ctx.attrs[self._name]  # type: ignore[attr-defined]

    def get(self) -> Value:
        """Read via PrimGetOp, returns typed Value."""
        from ..utils import typed_value
        from .morphisms import PrimGetOp

        return typed_value(self.value_type, PrimGetOp(self))

    def exists(self) -> BoolValue:
        """Check if name exists in context."""
        from ..values import BoolValue
        from .morphisms import PrimExistsOp

        return BoolValue(PrimExistsOp(self))
