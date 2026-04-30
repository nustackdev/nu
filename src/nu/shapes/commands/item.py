"""Item write commands — store / erase for an addressable item."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from nu import Nu
    from nu.shapes.refs import Ref


__all__ = [
    "ItemEraseCmd",
    "ItemStoreCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


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
