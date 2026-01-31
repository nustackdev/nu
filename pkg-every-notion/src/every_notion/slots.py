"""Notion slots - property type definitions for NotionTable.

Each slot type corresponds to a Notion property type:
- TitleSlot    → title (primary name column)
- TextSlot     → rich_text
- NumberSlot   → number
- SelectSlot   → select
- MultiSelectSlot → multi_select
- CheckboxSlot → checkbox
- DateSlot     → date
- EmailSlot    → email
- UrlSlot      → url
- PhoneSlot    → phone_number
- RelationSlot → relation
"""

from __future__ import annotations

from typing import Any

from .ref import CellRef


__all__ = [
    "CheckboxSlot",
    "DateSlot",
    "EmailSlot",
    "MultiSelectSlot",
    "NotionSlot",
    "NumberSlot",
    "PhoneSlot",
    "RelationSlot",
    "SelectSlot",
    "TextSlot",
    "TitleSlot",
    "UrlSlot",
]


class NotionSlot:
    """Base class for Notion property slots.

    Slots define the schema of a NotionTable and create CellRefs
    when accessed via row[name] or row.name.
    """

    notion_type: str  # Notion API property type
    name: str  # Property name (set by NotionTableMeta)

    def __init__(self, notion_type: str) -> None:
        self.notion_type = notion_type
        self.name = ""  # Will be set by metaclass

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when slot is assigned to a class attribute."""
        self.name = name

    def create_cell_ref(self, row_ref: Any) -> CellRef:
        """Create a CellRef for this slot on the given row."""
        return CellRef(
            row_ref=row_ref,
            property_name=self.name,
            notion_type=self.notion_type,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# =============================================================================
# CONCRETE SLOT TYPES
# =============================================================================


class TitleSlot(NotionSlot):
    """Slot for Notion title property (primary name column).

    Example:
        class Users(NotionTable):
            name = TitleSlot()  # The primary title column
    """

    def __init__(self) -> None:
        super().__init__("title")


class TextSlot(NotionSlot):
    """Slot for Notion rich_text property.

    Example:
        class Users(NotionTable):
            bio = TextSlot()
    """

    def __init__(self) -> None:
        super().__init__("rich_text")


class NumberSlot(NotionSlot):
    """Slot for Notion number property.

    Example:
        class Users(NotionTable):
            score = NumberSlot()
    """

    def __init__(self) -> None:
        super().__init__("number")


class SelectSlot(NotionSlot):
    """Slot for Notion select property (single choice).

    Example:
        class Users(NotionTable):
            status = SelectSlot()  # "Active", "Inactive", etc.
    """

    def __init__(self) -> None:
        super().__init__("select")


class MultiSelectSlot(NotionSlot):
    """Slot for Notion multi_select property (multiple choices).

    Example:
        class Users(NotionTable):
            tags = MultiSelectSlot()  # ["admin", "verified"]
    """

    def __init__(self) -> None:
        super().__init__("multi_select")


class CheckboxSlot(NotionSlot):
    """Slot for Notion checkbox property.

    Example:
        class Users(NotionTable):
            active = CheckboxSlot()
    """

    def __init__(self) -> None:
        super().__init__("checkbox")


class DateSlot(NotionSlot):
    """Slot for Notion date property.

    Example:
        class Users(NotionTable):
            created_at = DateSlot()
    """

    def __init__(self) -> None:
        super().__init__("date")


class EmailSlot(NotionSlot):
    """Slot for Notion email property.

    Example:
        class Users(NotionTable):
            email = EmailSlot()
    """

    def __init__(self) -> None:
        super().__init__("email")


class UrlSlot(NotionSlot):
    """Slot for Notion url property.

    Example:
        class Users(NotionTable):
            website = UrlSlot()
    """

    def __init__(self) -> None:
        super().__init__("url")


class PhoneSlot(NotionSlot):
    """Slot for Notion phone_number property.

    Example:
        class Users(NotionTable):
            phone = PhoneSlot()
    """

    def __init__(self) -> None:
        super().__init__("phone_number")


class RelationSlot(NotionSlot):
    """Slot for Notion relation property (links to other database).

    Example:
        class Orders(NotionTable):
            user = RelationSlot()  # Links to Users database
    """

    def __init__(self) -> None:
        super().__init__("relation")
