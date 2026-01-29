"""Notion refs - typed references to Notion locations.

These refs work with NotionTable (Shape subclass) and NotionSlots
to provide declarative access to Notion databases.

Hierarchy:
    NotionRef[T]      - Notion substrate base with resolve() and fetch()
    ├── TableRef      - reference to a database (from NotionTable class)
    ├── RowRef        - reference to a page/row in a table
    └── CellRef       - reference to a property/cell in a row

Core vocabulary:
    resolve(ctx) → dict     - build API parameters (database_id, page_id, property)
    fetch(ctx) → T          - call Notion API and extract value
    execute(ctx)            - Term interface, delegates to fetch()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from everyabc import EMPTY, Ref, Sentinel, Term


if TYPE_CHECKING:
    from .context import NotionContext
    from .ops import AddRowCmd, GetCellOp, RemoveRowCmd, SetCellCmd


__all__ = [
    "CellRef",
    "NotionRef",
    "RowRef",
    "TableRef",
]


class NotionRef[T](Ref[T], ABC):
    """Base class for all Notion refs.

    Notion refs resolve to API parameters (database_id, page_id, property_name)
    and fetch values by calling the Notion API.

    Subclasses must implement:
        resolve(ctx) - build dict of API parameters
        fetch(ctx) - call API and return value
    """

    __slots__ = ()

    @abstractmethod
    def resolve(self, ctx: NotionContext) -> dict[str, Any]:
        """Resolve ref to Notion API parameters.

        Returns:
            Dict with keys like database_id, page_id, property
        """
        ...

    @abstractmethod
    def fetch(self, ctx: NotionContext) -> T | Sentinel:
        """Fetch value from Notion API.

        Args:
            ctx: NotionContext with HTTP client

        Returns:
            The value, or Sentinel if not found
        """
        ...

    def execute(self, ctx: NotionContext) -> T | Sentinel:
        """Execute by fetching value. Term interface."""
        return self.fetch(ctx)

    @property
    def is_pure(self) -> bool:
        """Refs are pure (reading doesn't mutate)."""
        return True


class TableRef(NotionRef[list[dict[str, Any]]]):
    """Reference to a Notion database (table).

    Created automatically from NotionTable shape classes.
    fetch() returns list of all rows (pages) in the database.
    """

    __slots__ = ("_database_id", "_table_shape")

    def __init__(
        self,
        database_id: str,
        table_shape: type | None = None,
    ) -> None:
        self._database_id = database_id
        self._table_shape = table_shape

    @property
    def database_id(self) -> str:
        """The Notion database ID."""
        return self._database_id

    @property
    def table_shape(self) -> type | None:
        """The associated NotionTable shape class."""
        return self._table_shape

    def resolve(self, ctx: NotionContext) -> dict[str, Any]:
        """Resolve to database_id parameter."""
        return {"database_id": self._database_id}

    def fetch(self, ctx: NotionContext) -> list[dict[str, Any]]:
        """Fetch all rows from the database.

        Returns:
            List of page objects (rows)
        """
        return ctx.query_database(self._database_id)

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

    def __repr__(self) -> str:
        return f"TableRef({self._database_id!r})"


class RowRef(NotionRef[dict[str, Any]]):
    """Reference to a Notion page (row) in a database.

    Supports attribute access to cells via the table shape.
    fetch() returns the full page data.
    """

    __slots__ = ("_row_id", "_table_ref", "_table_shape")

    def __init__(
        self,
        table_ref: TableRef,
        row_id: str | Term[str],
        table_shape: type | None = None,
    ) -> None:
        self._table_ref = table_ref
        self._row_id = row_id
        self._table_shape = table_shape

    @property
    def table_ref(self) -> TableRef:
        """Parent table reference."""
        return self._table_ref

    @property
    def table_shape(self) -> type | None:
        """The associated NotionTable shape class."""
        return self._table_shape

    def resolve(self, ctx: NotionContext) -> dict[str, Any]:
        """Resolve to database_id + page_id parameters."""
        parent_params = self._table_ref.resolve(ctx)

        if isinstance(self._row_id, Term):
            row_id = self._row_id.execute(ctx)
        else:
            row_id = self._row_id

        return {**parent_params, "page_id": row_id}

    def fetch(self, ctx: NotionContext) -> dict[str, Any]:
        """Fetch the full page data.

        Returns:
            Page object with properties
        """
        resolved = self.resolve(ctx)
        return ctx.get_page(resolved["page_id"])

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

    def __repr__(self) -> str:
        return f"RowRef({self._table_ref!r}[{self._row_id!r}])"


class CellRef[T](NotionRef[T]):
    """Reference to a Notion property (cell) in a page.

    fetch() returns the extracted property value.
    """

    __slots__ = ("_notion_type", "_property_name", "_row_ref")

    def __init__(
        self,
        row_ref: RowRef,
        property_name: str | Term[str],
        notion_type: str | None = None,
    ) -> None:
        self._row_ref = row_ref
        self._property_name = property_name
        self._notion_type = notion_type

    @property
    def row_ref(self) -> RowRef:
        """Parent row reference."""
        return self._row_ref

    @property
    def notion_type(self) -> str | None:
        """The Notion property type (title, rich_text, number, etc.)."""
        return self._notion_type

    def resolve(self, ctx: NotionContext) -> dict[str, Any]:
        """Resolve to database_id + page_id + property parameters."""
        parent_params = self._row_ref.resolve(ctx)

        if isinstance(self._property_name, Term):
            prop_name = self._property_name.execute(ctx)
        else:
            prop_name = self._property_name

        return {**parent_params, "property": prop_name}

    def fetch(self, ctx: NotionContext) -> T | Sentinel:
        """Fetch the cell value from Notion.

        Returns:
            The extracted property value, or EMPTY if not found
        """
        from .ops import extract_property_value

        resolved = self.resolve(ctx)
        page_id = resolved["page_id"]
        prop_name = resolved["property"]

        page_data = ctx.get_page(page_id)
        properties = page_data.get("properties", {})

        if prop_name not in properties:
            return EMPTY

        return extract_property_value(properties[prop_name])

    def get(self) -> GetCellOp:
        """Create operation to get cell value.

        For compatibility with operation pattern.
        Prefer using fetch() directly.
        """
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

    def __repr__(self) -> str:
        return f"CellRef({self._row_ref!r}.{self._property_name!r})"


# Import at bottom to avoid circular imports
