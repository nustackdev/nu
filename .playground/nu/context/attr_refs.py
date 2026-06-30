"""AttrRef - flat name-based lookup from Context.

Resolves a name directly from `ctx.attrs`. Typed variants mix in the
Form so you can chain operations on the ref.

Name can be a plain string or a Nu that resolves to a string.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.forms.collections import DictForm, FrozenSetForm, ListForm, SetForm, TupleForm
from nu.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, StrForm
from nu.queries.literal import Literal
from nu.terms.ref import Ref
from nu.terms.sentinels import EMPTY
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import StrArg
    from nu.terms.protocol import Nu

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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class AttrRef[T](Ref[T]):
    """Attr ref - flat name-based lookup from Context.

    Resolves a name from `ctx.attrs`. Name can be a plain string (static)
    or a Nu (dynamic, resolved at eval time).

    Args:
        name: ctx.attrs key. Plain string or Nu resolving to string.

    Example::

        AttrRef("error")              # static key
        AttrRef(some_computed_key)    # dynamic key
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, name: StrArg) -> None:
        super().__init__()
        self._raw_name: str | None = name if isinstance(name, str) else None
        # Wrap dynamic names so we can drive them through the runtime.
        from nu.terms.nu import NuBase

        if isinstance(name, NuBase):
            self._name_nu: Nu = name  # type: ignore[assignment]
        else:
            self._name_nu = Literal(name)  # type: ignore[assignment]

    @property
    def name(self) -> str | None:
        """Static name tag, or None if dynamic."""
        return self._raw_name

    def _resolve_name_sync(self, ctx: Context) -> str:
        if self._raw_name is not None:
            return self._raw_name
        return self._name_nu.eval(ctx)

    async def _resolve_name_async(self, ctx: Context) -> str:
        if self._raw_name is not None:
            return self._raw_name
        return await self._name_nu.aeval(ctx)

    def eval(self, ctx: Context) -> Any:  # noqa: ANN401, D102
        key = self._resolve_name_sync(ctx)
        return (
            ctx.attrs.get(key, EMPTY)
            if hasattr(ctx.attrs, "get")
            # type: ignore[union-attr]
            else (
                ctx.attrs[key] if key in ctx.attrs else EMPTY  # type: ignore[operator]
            )
        )

    async def aeval(self, ctx: Context) -> Any:  # noqa: ANN401, D102
        key = await self._resolve_name_async(ctx)
        return (
            ctx.attrs.get(key, EMPTY)
            if hasattr(ctx.attrs, "get")
            # type: ignore[union-attr]
            else (
                ctx.attrs[key] if key in ctx.attrs else EMPTY  # type: ignore[operator]
            )
        )

    def exists(self) -> BoolForm:
        """Check if name exists in context."""
        from .attr_ops import AttrExistsOp

        return BoolForm(AttrExistsOp(self))


# =========================================================================
# PRIMITIVE TYPED ATTR REFS
# =========================================================================


class IntAttrRef(AttrRef[int], IntForm):
    """Int attr ref with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class FloatAttrRef(AttrRef[float], FloatForm):
    """Float attr ref with full numeric interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class StrAttrRef(AttrRef[str], StrForm):
    """Str attr ref with full string interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class BoolAttrRef(AttrRef[bool], BoolForm):
    """Bool attr ref with full logical interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class BytesAttrRef(AttrRef[bytes], BytesForm):
    """Bytes attr ref with full bytes interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class AnyAttrRef(AttrRef[object], AnyForm):
    """Any attr ref with dynamic interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


# =========================================================================
# COMPOSITE TYPED ATTR REFS
# =========================================================================


class ListAttrRef(AttrRef[list], ListForm):
    """List attr ref with full list interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class DictAttrRef(AttrRef[dict], DictForm):
    """Dict attr ref with full dict interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class SetAttrRef(AttrRef[set], SetForm):
    """Set attr ref with full set interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class FrozenSetAttrRef(AttrRef[frozenset], FrozenSetForm):
    """FrozenSet attr ref with full frozenset interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH


class TupleAttrRef(AttrRef[tuple], TupleForm):
    """Tuple attr ref with full tuple interface."""

    support: ClassVar[frozenset[Mode]] = _BOTH
