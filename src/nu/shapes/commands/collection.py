"""Collection write commands — store / erase for an addressable collection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from nu import Nu
    from nu.shapes.refs import Ref


__all__ = [
    "CollectionEraseCmd",
    "CollectionStoreCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class CollectionStoreCmd(ScalarCommand):
    """Write collection to parent: parent[address] = data."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: Ref, data: Nu) -> None:
        super().__init__(ref, data)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        data = await runtime.afirst(self._children[1], ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")
        ref = self._children[0]
        parent = await ref.afetch_parent(ctx)
        address = await ref.aresolve_address(ctx)
        parent[address] = data

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        data = runtime.first(self._children[1], ctx)
        if is_sentinel(data):
            raise ValueError(f"Cannot store sentinel value: {data}")
        ref = self._children[0]
        parent = ref.fetch_parent(ctx)
        address = ref.resolve_address(ctx)
        parent[address] = data

    def __repr__(self) -> str:
        return f"CollectionStoreCmd({self._children[0]!r}, {self._children[1]!r})"


class CollectionEraseCmd(ScalarCommand):
    """Delete collection from parent: del parent[address]."""

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
        return f"CollectionEraseCmd({self._children[0]!r})"
