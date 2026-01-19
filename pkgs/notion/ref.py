"""Notion refs - typed references to Notion locations.

These refs work with NotionTable (Shape subclass) and NotionSlots
to provide declarative access to Notion databases.

Hierarchy:
    NotionRef (base)
    ├── TableRef      - reference to a database (from NotionTable class)
    ├── RowRef        - reference to a page/row in a table
    └── CellRef       - reference to a property/cell in a row
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from everyterm.term import Ref, Term


if TYPE_CHECKING:
    from .context import NotionContext


__all__ = [
    "CellRef",
    "NotionRef",
    "RowRef",
    "TableRef",
]

T = TypeVar("T")


class NotionRef(Ref[T], ABC, Generic[T]):
    """Base class for Notion refs.

    Unlike KV refs which resolve to paths, Notion refs resolve to
    API parameters (database_id, page_id, property_name).
    """

    @abstractmethod
    def resolve(self, context: NotionContext) -> dict[str, Any]:
        """Resolve ref to Notion API parameters."""
        ...


class TableRef(NotionRef[list[dict[str, Any]]]):
    """Reference to a Notion database (table).

    Created automatically from NotionTable shape classes.
    """

    def __init__(
        self,
        database_id: str,
        table_shape: type | None = None,
    ) -> None:
        super().__init__(parent_ref=None, owner_shape=None)
        self._database_id = database_id
        self._table_shape = table_shape

    def resolve(self, context: NotionContext) -> dict[str, Any]:
        return {"database_id": self._database_id}

    def __getitem__(self, row_id: str | Term[str]) -> RowRef:
        """Get a row ref by page ID."""
        return RowRef(
            table_ref=self,
            row_id=row_id,
            table_shape=self._table_shape,
        )

    def add_row(self, **properties: Any) -> AddRowCmd:
        """Create command to add a new row with keyword arguments.

        Args:
            **properties: Column values as keyword arguments

        Example:
            Users.add_row(name="Alice", email="alice@example.com")
        """
        from .ops import AddRowCmd

        return AddRowCmd(
            table_ref=self,
            properties=properties,
            table_shape=self._table_shape,
        )

    def execute(self, context: NotionContext) -> list[dict[str, Any]]:
        """Execute: query all rows from table."""
        resolved = self.resolve(context)
        return context.query_database(resolved["database_id"])

    def __repr__(self) -> str:
        return f"TableRef({self._database_id!r})"


class RowRef(NotionRef[dict[str, Any]]):
    """Reference to a Notion page (row) in a database.

    Supports attribute access to cells via the table shape.
    """

    def __init__(
        self,
        table_ref: TableRef,
        row_id: str | Term[str],
        table_shape: type | None = None,
    ) -> None:
        super().__init__(parent_ref=table_ref, owner_shape=None)
        self.table_ref = table_ref
        self._row_id = row_id
        self._table_shape = table_shape

    def resolve(self, context: NotionContext) -> dict[str, Any]:
        parent_params = self.table_ref.resolve(context)

        if isinstance(self._row_id, Term):
            row_id = self._row_id.execute(context)
        else:
            row_id = self._row_id

        return {**parent_params, "page_id": row_id}

    def __getitem__(self, property_name: str) -> CellRef:
        """Get a cell ref by property name."""
        # Try to get property type from shape
        prop_type = None
        if self._table_shape is not None:
            slot = getattr(self._table_shape, property_name, None)
            if slot is not None and hasattr(slot, "notion_type"):
                prop_type = slot.notion_type

        return CellRef(
            row_ref=self,
            property_name=property_name,
            notion_type=prop_type,
        )

    def __getattr__(self, name: str) -> CellRef:
        """Attribute access to cells: row.Name, row.Email, etc."""
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    def remove(self) -> RemoveRowCmd:
        """Create command to remove (archive) this row."""
        from .ops import RemoveRowCmd

        return RemoveRowCmd(row_ref=self)

    def execute(self, context: NotionContext) -> dict[str, Any]:
        """Execute: get full row data."""
        resolved = self.resolve(context)
        return context.get_page(resolved["page_id"])

    def __repr__(self) -> str:
        return f"RowRef({self.table_ref!r}[{self._row_id!r}])"


class CellRef(NotionRef[Any], Generic[T]):
    """Reference to a Notion property (cell) in a page."""

    def __init__(
        self,
        row_ref: RowRef,
        property_name: str | Term[str],
        notion_type: str | None = None,
    ) -> None:
        super().__init__(parent_ref=row_ref, owner_shape=None)
        self.row_ref = row_ref
        self._property_name = property_name
        self._notion_type = notion_type

    def resolve(self, context: NotionContext) -> dict[str, Any]:
        parent_params = self.row_ref.resolve(context)

        if isinstance(self._property_name, Term):
            prop_name = self._property_name.execute(context)
        else:
            prop_name = self._property_name

        return {**parent_params, "property": prop_name}

    def get(self) -> GetCellOp:
        """Create operation to get cell value."""
        from .ops import GetCellOp

        return GetCellOp(cell_ref=self)

    def set(self, value: Any | Term[Any]) -> SetCellCmd:
        """Create command to set cell value."""
        from .ops import SetCellCmd

        return SetCellCmd(
            cell_ref=self,
            value=value,
            prop_type=self._notion_type,
        )

    def execute(self, context: NotionContext) -> Any:
        """Execute: get cell value."""
        return self.get().execute(context)

    def __repr__(self) -> str:
        return f"CellRef({self.row_ref!r}.{self._property_name!r})"


# Import at bottom to avoid circular imports
from .ops import AddRowCmd, GetCellOp, RemoveRowCmd, SetCellCmd
