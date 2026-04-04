"""AttrRef — flat name-based lookup from Context.

AttrRef is the simplest substrate: resolves a name directly from ctx.attrs.
Typed variants (IntAttrRef, StrAttrRef, etc.) inherit Interface mixins
so you can chain operations directly on the ref.

Name can be a plain string or a Nu that resolves to a string.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.terms import Nu, Ref, Sentinel
from nu.utils import ensure_nu


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import StrArg, Value

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

    Name can be a plain string (static) or a Nu (dynamic, resolved at
    execution time).

    Args:
        name: ctx.attrs key. Plain string or Nu resolving to string.

    Example::

        AttrRef("error")                    # static key
        AttrRef(some_computed_key)           # dynamic key
    """

    value_type: type = object

    def __init__(self, name: StrArg) -> None:
        """Initialize with name tag.

        Args:
            name: ctx.attrs key. Plain string or Nu resolving to string.
        """
        super().__init__()
        self._raw_name: str | None = name if isinstance(name, str) else None
        self._name_nu: Nu = ensure_nu(name)

    @property
    def name(self) -> str | None:
        """Static name tag, or None if dynamic."""
        return self._raw_name

    async def _resolve_name(self, ctx: Context) -> str:
        """Resolve the name — fast path for static, execute for dynamic."""
        if self._raw_name is not None:
            return self._raw_name
        return await self._name_nu.execute(ctx)

    async def resolve(self, ctx: Context) -> str:
        """Resolve to the name string."""
        return await self._resolve_name(ctx)

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value from context attrs by name."""
        key = await self._resolve_name(ctx)
        return ctx.attrs[key]  # type: ignore[attr-defined]

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
