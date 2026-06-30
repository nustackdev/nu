"""Item read queries — load / exists / missing for an addressable item."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.shapes.refs import Ref


__all__ = [
    "ItemExists",
    "ItemLoad",
    "ItemMissing",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ItemLoad(ScalarQuery):
    """Read item from collection. Returns EMPTY if missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]

    def __repr__(self) -> str:
        return f"ItemLoad({self._children[0]!r})"


class ItemExists(ScalarQuery):
    """Check if item exists."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"ItemExists({self._children[0]!r})"


class ItemMissing(ScalarQuery):
    """Check if item is missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"ItemMissing({self._children[0]!r})"
