"""Item access ops - CRUD for items within collections.

ItemLoadOp:    Read item value - yields ref's value
ItemStoreCmd:  Write item value - parent[address] = value
ItemEraseCmd:  Delete item - del parent[address]
ItemExistsOp:  Check if item exists
ItemMissingOp: Check if item is missing

READ ops go through ref.aopen (Snapshot wrapper).
WRITE ops use children[0] as Ref directly (inside Transaction wrapper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from nu import Nu
    from nu.shapes.refs import Ref


__all__ = [
    "ItemEraseCmd",
    "ItemExistsOp",
    "ItemLoadOp",
    "ItemMissingOp",
    "ItemStoreCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ItemLoadOp(ScalarQuery):
    """Read item from collection. Returns EMPTY if missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]

    def __repr__(self) -> str:
        return f"ItemLoadOp({self._children[0]!r})"


class ItemStoreCmd(ScalarCommand):
    """Write item to collection: parent[address] = value."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref, value: Nu) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        ref = self._children[0]
        parent = await ref.afetch_parent(ctx)
        address = await ref.aresolve_address(ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        ref = self._children[0]
        parent = ref.fetch_parent(ctx)
        address = ref.resolve_address(ctx)
        value = runtime.first(self._children[1], ctx)
        if is_sentinel(value):
            raise ValueError(f"Cannot store sentinel value: {value}")
        parent[address] = value

    def __repr__(self) -> str:
        return f"ItemStoreCmd({self._children[0]!r}, {self._children[1]!r})"


class ItemEraseCmd(ScalarCommand):
    """Delete item from collection: del parent[address]."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        ref = self._children[0]
        parent = await ref.afetch_parent(ctx)
        address = await ref.aresolve_address(ctx)
        del parent[address]

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        ref = self._children[0]
        parent = ref.fetch_parent(ctx)
        address = ref.resolve_address(ctx)
        del parent[address]

    def __repr__(self) -> str:
        return f"ItemEraseCmd({self._children[0]!r})"


class ItemExistsOp(ScalarQuery):
    """Check if item exists."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"ItemExistsOp({self._children[0]!r})"


class ItemMissingOp(ScalarQuery):
    """Check if item is missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"ItemMissingOp({self._children[0]!r})"
