"""Notion integration for everybase.

Provides Shape-based declarative access to Notion databases.

Example:
    from everybase.notion import (
        NotionContext,
        NotionTable,
        TitleSlot,
        EmailSlot,
        NumberSlot,
        SelectSlot,
    )

    # Define schema
    class Users(NotionTable):
        database_id = "your-database-id"

        name = TitleSlot()
        email = EmailSlot()
        score = NumberSlot()
        status = SelectSlot()

    # Create context
    with NotionContext.create(api_key="secret_xxx") as ctx:
        # Add a row
        Users.add_row(name="Alice", email="alice@example.com", score=95).execute(ctx)

        # Get a cell value
        name = Users["page-id"].name.get().execute(ctx)

        # Update a cell
        Users["page-id"].email.set("new@example.com").execute(ctx)

        # Remove a row (archives it)
        Users["page-id"].remove().execute(ctx)

        # Query all rows
        rows = Users.execute(ctx)
"""

from .context import NotionContext
from .ops import AddRowCmd, GetCellOp, RemoveRowCmd, SetCellCmd
from .ref import CellRef, NotionRef, RowRef, TableRef
from .shape import NotionTable
from .slots import (
    CheckboxSlot,
    DateSlot,
    EmailSlot,
    MultiSelectSlot,
    NotionSlot,
    NumberSlot,
    PhoneSlot,
    RelationSlot,
    SelectSlot,
    TextSlot,
    TitleSlot,
    UrlSlot,
)


__all__ = [
    # Context
    "NotionContext",
    # Shape
    "NotionTable",
    # Slots
    "NotionSlot",
    "TitleSlot",
    "TextSlot",
    "NumberSlot",
    "SelectSlot",
    "MultiSelectSlot",
    "CheckboxSlot",
    "DateSlot",
    "EmailSlot",
    "UrlSlot",
    "PhoneSlot",
    "RelationSlot",
    # Refs
    "NotionRef",
    "TableRef",
    "RowRef",
    "CellRef",
    # Ops
    "AddRowCmd",
    "RemoveRowCmd",
    "GetCellOp",
    "SetCellCmd",
]
