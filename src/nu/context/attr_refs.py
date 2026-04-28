"""AttrRef — flat name-based lookup from Context.

AttrRef is the simplest substrate: resolves a name directly from ctx.attrs.
Typed variants mix in Interface so you can chain operations directly on the ref.

Name can be a plain string or a Nu that resolves to a string.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.collections import DictI, FrozenSetI, ListI, SetI, TupleI
from nu.primitives import AnyI, BoolI, BytesI, FloatI, IntI, StrI
from nu.terms import Literal, Mode, Nu, Ref, Sentinel


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import StrArg

__all__ = [
    "AnyAttrRef",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "SetAttrRef",
    "StrAttrRef",
    "TupleAttrRef",
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

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, name: StrArg) -> None:
        super().__init__()
        self._raw_name: str | None = name if isinstance(name, str) else None
        self._name_nu: Nu = name if isinstance(name, Nu) else Literal(name)

    @property
    def name(self) -> str | None:
        """Static name tag, or None if dynamic."""
        return self._raw_name

    async def _resolve_name(self, ctx: Context) -> str:
        """Resolve the name — fast path for static, execute for dynamic."""
        if self._raw_name is not None:
            return self._raw_name
        return await self._name_ctx.aexecute()

    async def aresolve(self, ctx: Context) -> str:
        """Resolve to the name string."""
        return await self._resolve_name(ctx)

    async def afetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value from context attrs by name."""
        key = await self._resolve_name(ctx)
        return ctx.attrs[key]  # type: ignore[attr-defined]

    def _resolve_name_sync(self, ctx: Context) -> str:
        """Sync counterpart of `_resolve_name`."""
        if self._raw_name is not None:
            return self._raw_name
        return self._name_nu.first(ctx)

    def resolve(self, ctx: Context) -> str:
        """Sync counterpart of `aresolve`."""
        return self._resolve_name_sync(ctx)

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Sync counterpart of `afetch`."""
        key = self._resolve_name_sync(ctx)
        return ctx.attrs[key]  # type: ignore[attr-defined]

    def exists(self) -> BoolI:
        """Check if name exists in context."""
        from .attr_ops import AttrExistsOp

        return BoolI(AttrExistsOp(self))


# =========================================================================
# PRIMITIVE TYPED ATTR REFS
# =========================================================================


class IntAttrRef(AttrRef[int], IntI):
    """Int attr ref with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class FloatAttrRef(AttrRef[float], FloatI):
    """Float attr ref with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class StrAttrRef(AttrRef[str], StrI):
    """Str attr ref with full string interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class BoolAttrRef(AttrRef[bool], BoolI):
    """Bool attr ref with full logical interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class BytesAttrRef(AttrRef[bytes], BytesI):
    """Bytes attr ref with full bytes interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class AnyAttrRef(AttrRef[object], AnyI):
    """Any attr ref with dynamic interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


# =========================================================================
# COMPOSITE TYPED ATTR REFS
# =========================================================================


class ListAttrRef(AttrRef[list], ListI):
    """List attr ref with full list interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class DictAttrRef(AttrRef[dict], DictI):
    """Dict attr ref with full dict interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class SetAttrRef(AttrRef[set], SetI):
    """Set attr ref with full set interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class FrozenSetAttrRef(AttrRef[frozenset], FrozenSetI):
    """FrozenSet attr ref with full frozenset interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


class TupleAttrRef(AttrRef[tuple], TupleI):
    """Tuple attr ref with full tuple interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
