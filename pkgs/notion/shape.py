"""NotionTable - declarative Notion database schema.

NotionTable is a Shape-like class that defines the schema of a Notion
database. It uses slots to define property types and provides ref-based
access to rows and cells.

Example:
    class Users(NotionTable):
        database_id = "abc123..."

        name = TitleSlot()
        email = EmailSlot()
        status = SelectSlot()
        score = NumberSlot()

    # Access rows
    Users["page-id"].name.get().execute(ctx)
    Users["page-id"].email.set("new@example.com").execute(ctx)

    # Add rows
    Users.add_row(name="Alice", email="alice@example.com").execute(ctx)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from .ref import RowRef, TableRef
from .slots import NotionSlot


if TYPE_CHECKING:
    from .ops import AddRowCmd


__all__ = [
    "NotionTable",
]


class NotionTableMeta(type):
    """Metaclass for NotionTable that sets up slots and table ref."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> NotionTableMeta:
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip for base NotionTable class
        if name == "NotionTable":
            return cls

        # Collect slots from class attributes
        slots: dict[str, NotionSlot] = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, NotionSlot):
                attr_value.name = attr_name
                slots[attr_name] = attr_value

        # Also collect from base classes
        for base in bases:
            if hasattr(base, "_notion_slots"):
                for slot_name, slot in base._notion_slots.items():
                    if slot_name not in slots:
                        slots[slot_name] = slot

        cls._notion_slots = slots

        # Create table ref if database_id is defined
        database_id = namespace.get("database_id")
        if database_id:
            cls._table_ref = TableRef(database_id=database_id, table_shape=cls)

        return cls

    def __getitem__(cls, row_id: str) -> RowRef:
        """Access a row by page ID: Users["page-id"]."""
        if not hasattr(cls, "_table_ref"):
            raise ValueError(f"{cls.__name__} has no database_id defined")
        return cls._table_ref[row_id]

    def __getattr__(cls, name: str) -> Any:
        """Allow accessing slots as class attributes for type hints."""
        if name.startswith("_"):
            raise AttributeError(name)
        if hasattr(cls, "_notion_slots") and name in cls._notion_slots:
            return cls._notion_slots[name]
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")


class NotionTable(metaclass=NotionTableMeta):
    """Base class for Notion database schemas.

    Subclass this and define:
    - database_id: The Notion database ID
    - Slots for each property/column

    Example:
        class Users(NotionTable):
            database_id = "abc123-def456..."

            name = TitleSlot()
            email = EmailSlot()
            status = SelectSlot()

        # Query all rows
        rows = Users.execute(ctx)

        # Access specific row
        user = Users["page-id"]
        name = user.name.get().execute(ctx)

        # Update cell
        user.email.set("new@example.com").execute(ctx)

        # Add new row
        Users.add_row(name="Bob", email="bob@example.com").execute(ctx)
    """

    database_id: ClassVar[str]
    _table_ref: ClassVar[TableRef]
    _notion_slots: ClassVar[dict[str, NotionSlot]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate subclass has required attributes."""
        super().__init_subclass__(**kwargs)
        # database_id validation happens in metaclass

    @classmethod
    def add_row(cls, **properties: Any) -> AddRowCmd:
        """Create command to add a new row.

        Args:
            **properties: Column values matching slot names

        Example:
            Users.add_row(name="Alice", email="alice@example.com")
        """
        if not hasattr(cls, "_table_ref"):
            raise ValueError(f"{cls.__name__} has no database_id defined")
        return cls._table_ref.add_row(**properties)

    @classmethod
    def execute(cls, context: Any) -> list[dict[str, Any]]:
        """Execute: query all rows from the table."""
        if not hasattr(cls, "_table_ref"):
            raise ValueError(f"{cls.__name__} has no database_id defined")
        return cls._table_ref.execute(context)
