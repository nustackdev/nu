"""TableRef: tabular data with columns + positional rows. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.append import Append
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TableRef"]


class TableRef(NudleRef):
    """Display-only table. Value is `{columns: list[str], rows: list[list]}`."""

    columns: ClassVar[list[str]] = []
    striped: ClassVar[bool] = True
    dense: ClassVar[bool] = False
    max_rows: ClassVar[int] = 0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "columns": list(cls.columns),
            "striped": cls.striped,
            "dense": cls.dense,
            "max_rows": cls.max_rows,
        }

    def store(self, table: Nu | dict[str, Any]) -> Nu:
        return Write(self, table)

    def clear(self) -> Nu:
        return Write(self, {"rows": []})

    def append(self, row: Nu | list[Any]) -> Nu:
        return Append(self, row)
