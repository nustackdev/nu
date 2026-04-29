"""Collection-level ops - get, set, delete, exists, missing.

Same logic as item ops but distinct tree node types, so substrates
can match on CollectionLoadOp vs ItemLoadOp for type-specific deformations
(e.g. PV primitive optimizations only target Item* variants).

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
    "CollectionEraseCmd",
    "CollectionExistsOp",
    "CollectionExtractOp",
    "CollectionLoadOp",
    "CollectionMissingOp",
    "CollectionStoreCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class CollectionLoadOp(ScalarQuery):
    """Read collection from parent. Returns EMPTY if missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]

    def __repr__(self) -> str:
        return f"CollectionLoadOp({self._children[0]!r})"


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


class CollectionExtractOp(ScalarQuery):
    """Materialize the full value tree at the ref via view.extract().

    Recursive read — for container views walks the subtree and returns
    a plain Python value (dict / list / nested mix). Counterpart to a
    flat fetch.

    The ref must implement:
        fetch(ctx) / afetch(ctx) -> view with .extract() method
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        view = ops[0]
        if is_sentinel(view):
            return view
        if hasattr(view, "eager"):
            view = view.eager
        return view.extract()

    def __repr__(self) -> str:
        return f"CollectionExtractOp({self._children[0]!r})"


class CollectionExistsOp(ScalarQuery):
    """Check if collection exists: not is_sentinel(ref value)."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"CollectionExistsOp({self._children[0]!r})"


class CollectionMissingOp(ScalarQuery):
    """Check if collection is missing: is_sentinel(ref value)."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"CollectionMissingOp({self._children[0]!r})"
