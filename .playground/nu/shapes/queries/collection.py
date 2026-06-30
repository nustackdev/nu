"""Collection read queries — load / exists / missing / extract.

Same logic as item queries but distinct node types, so substrates can match
on CollectionLoad vs ItemLoad for type-specific deformations (e.g. PV
primitive optimisations only target item variants).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import is_sentinel
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.shapes.refs import Ref


__all__ = [
    "CollectionExists",
    "CollectionExtract",
    "CollectionLoad",
    "CollectionMissing",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class CollectionLoad(ScalarQuery):
    """Read collection from parent. Returns EMPTY if missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0]

    def __repr__(self) -> str:
        return f"CollectionLoad({self._children[0]!r})"


class CollectionExtract(ScalarQuery):
    """Materialise the full value tree at the ref via view.extract().

    Recursive read — for container views walks the subtree and returns a
    plain Python value (dict / list / nested mix). Counterpart to a flat
    fetch. The ref must implement fetch/afetch returning a view with
    .extract().
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
        return f"CollectionExtract({self._children[0]!r})"


class CollectionExists(ScalarQuery):
    """Check if collection exists."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"CollectionExists({self._children[0]!r})"


class CollectionMissing(ScalarQuery):
    """Check if collection is missing."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, ref: Ref) -> None:
        super().__init__(ref)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_sentinel(ops[0])

    def __repr__(self) -> str:
        return f"CollectionMissing({self._children[0]!r})"
