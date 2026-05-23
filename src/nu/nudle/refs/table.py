"""TableRef: tabular data with columns + positional rows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.queries.record import Record

from ..interactions.append import Append
from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["TableRef"]


class TableRef(NudleRef):
    """Tabular data; display by default, optional sortable headers and row click."""

    columns: ClassVar[list[str]] = []
    striped: ClassVar[bool] = True
    dense: ClassVar[bool] = False
    max_rows: ClassVar[int] = 0
    sort_column: ClassVar[str] = ""
    sort_direction: ClassVar[str] = "asc"
    clickable_rows: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "columns": list(cls.columns),
            "striped": cls.striped,
            "dense": cls.dense,
            "max_rows": cls.max_rows,
            "sort_column": cls.sort_column,
            "sort_direction": cls.sort_direction,
            "clickable_rows": cls.clickable_rows,
        }

    def store(self, table: Nu | dict[str, Any]) -> Nu:
        return Write(self, table)

    def clear(self) -> Nu:
        return Write(self, Record(rows=[]))

    def append(self, row: Nu | list[Any]) -> Nu:
        return Append(self, row)

    def store_sort(self, column: Nu | str, direction: Nu | str) -> Nu:
        return Write(self, Record(sort_column=column, sort_direction=direction))

    def row_clicked(self) -> Changed:
        return Changed(self)
