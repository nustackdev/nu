"""Record - dict literal whose values are Nu expressions.

Each kwarg becomes a field. Field values are evaluated in the current
ctx and zipped back with their names into a fresh dict.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = ["Record"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Record(ScalarQuery):
    """Dict literal: `Record(a=x, b=y)` -> `{"a": eval(x), "b": eval(y)}`."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    _names: tuple[str, ...]

    def __init__(self, **fields: Any) -> None:  # noqa: ANN401
        self._names = tuple(fields.keys())
        super().__init__(*fields.values())

    def _apply(self, ctx: Any, ops: list[Any]) -> dict[str, Any]:  # noqa: ANN401
        return dict(zip(self._names, ops, strict=True))
