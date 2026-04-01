"""AttrRef — flat name-based lookup from Context.

AttrRef is the simplest substrate: resolves a name directly from ctx.attrs.
Typed variants (IntAttrRef, StrAttrRef, etc.) inherit Interface mixins
so you can chain operations directly on the ref.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Ref, Sentinel


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Value

    from nu.interfaces import BoolI

__all__ = [
    "AnyAttrRef",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "FloatAttrRef",
    "IntAttrRef",
    "StrAttrRef",
]


class AttrRef[T](Ref[T]):
    """Attr ref — flat name-based lookup from Context.

    The simplest substrate: resolves a name directly from ctx.attrs.
    No parent chain, no shape, no hierarchical addressing.

    Usage:
        ref = AttrRef("error")
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

    async def resolve(self, ctx: Context) -> str:
        """Resolve to the name string."""
        return self._name

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value from context attrs by name."""
        return ctx.attrs[self._name]  # type: ignore[attr-defined]

    def get(self) -> Value:
        """Read via AttrGetOp, returns typed Interface."""
        from ..utils import typed_value
        from .attr_ops import AttrGetOp

        return typed_value(self.value_type, AttrGetOp(self))

    def exists(self) -> BoolI:
        """Check if name exists in context."""
        from nu.interfaces import BoolI
        from .attr_ops import AttrExistsOp

        return BoolI(AttrExistsOp(self))


# =========================================================================
# TYPED ATTR REFS
# =========================================================================


class IntAttrRef(AttrRef[int]):
    """Int attr ref. Inherits IntI methods via get()."""

    value_type = int

    def get(self) -> IntI:  # noqa: F821
        from nu.interfaces import IntI
        from .attr_ops import AttrGetOp

        return IntI(AttrGetOp(self))


class FloatAttrRef(AttrRef[float]):
    """Float attr ref."""

    value_type = float

    def get(self) -> FloatI:  # noqa: F821
        from nu.interfaces import FloatI
        from .attr_ops import AttrGetOp

        return FloatI(AttrGetOp(self))


class StrAttrRef(AttrRef[str]):
    """Str attr ref."""

    value_type = str

    def get(self) -> StrI:  # noqa: F821
        from nu.interfaces import StrI
        from .attr_ops import AttrGetOp

        return StrI(AttrGetOp(self))


class BoolAttrRef(AttrRef[bool]):
    """Bool attr ref."""

    value_type = bool

    def get(self) -> BoolI:  # noqa: F821
        from nu.interfaces import BoolI
        from .attr_ops import AttrGetOp

        return BoolI(AttrGetOp(self))


class BytesAttrRef(AttrRef[bytes]):
    """Bytes attr ref."""

    value_type = bytes

    def get(self) -> BytesI:  # noqa: F821
        from nu.interfaces import BytesI
        from .attr_ops import AttrGetOp

        return BytesI(AttrGetOp(self))


class AnyAttrRef(AttrRef[object]):
    """Any attr ref. Dynamic type."""

    value_type = object

    def get(self) -> AnyI:  # noqa: F821
        from nu.interfaces import AnyI
        from .attr_ops import AttrGetOp

        return AnyI(AttrGetOp(self))
