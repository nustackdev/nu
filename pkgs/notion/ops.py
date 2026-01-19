"""Notion operations and commands.

Operations (read):
    - GetCellOp: Read a cell value from a row

Commands (write):
    - AddRowCmd: Add a new row to a table
    - RemoveRowCmd: Remove (archive) a row
    - SetCellCmd: Update a cell value
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyterm.term import Command, Operation, Term


if TYPE_CHECKING:
    from .context import NotionContext
    from .ref import CellRef, RowRef, TableRef
    from .slots import NotionSlot


__all__ = [
    "AddRowCmd",
    "GetCellOp",
    "RemoveRowCmd",
    "SetCellCmd",
]


# =============================================================================
# VALUE CONVERSION HELPERS
# =============================================================================


def extract_property_value(property_data: dict[str, Any]) -> Any:
    """Extract plain value from Notion property structure."""
    prop_type = property_data.get("type")

    if prop_type == "title":
        title_parts = property_data.get("title", [])
        return "".join(part.get("plain_text", "") for part in title_parts)

    elif prop_type == "rich_text":
        text_parts = property_data.get("rich_text", [])
        return "".join(part.get("plain_text", "") for part in text_parts)

    elif prop_type == "number":
        return property_data.get("number")

    elif prop_type == "select":
        select = property_data.get("select")
        return select.get("name") if select else None

    elif prop_type == "multi_select":
        options = property_data.get("multi_select", [])
        return [opt.get("name") for opt in options]

    elif prop_type == "checkbox":
        return property_data.get("checkbox")

    elif prop_type == "date":
        date_obj = property_data.get("date")
        return date_obj.get("start") if date_obj else None

    elif prop_type == "url":
        return property_data.get("url")

    elif prop_type == "email":
        return property_data.get("email")

    elif prop_type == "phone_number":
        return property_data.get("phone_number")

    elif prop_type == "relation":
        relations = property_data.get("relation", [])
        return [rel.get("id") for rel in relations]

    elif prop_type == "formula":
        formula = property_data.get("formula", {})
        formula_type = formula.get("type")
        return formula.get(formula_type)

    elif prop_type == "rollup":
        rollup = property_data.get("rollup", {})
        rollup_type = rollup.get("type")
        return rollup.get(rollup_type)

    return property_data


def build_property_value(value: Any, prop_type: str | None = None) -> dict[str, Any]:
    """Build Notion property structure from plain value."""
    # Infer type if not provided
    if prop_type is None:
        if isinstance(value, bool):
            prop_type = "checkbox"
        elif isinstance(value, (int, float)):
            prop_type = "number"
        elif isinstance(value, str):
            prop_type = "rich_text"
        elif isinstance(value, list):
            if value and isinstance(value[0], str):
                if len(value[0]) == 36 and "-" in value[0]:
                    prop_type = "relation"
                else:
                    prop_type = "multi_select"
            else:
                prop_type = "multi_select"
        else:
            prop_type = "rich_text"
            value = str(value)

    # Build property structure
    if prop_type == "title":
        return {"title": [{"text": {"content": str(value)}}]}

    elif prop_type == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}

    elif prop_type == "number":
        return {"number": value}

    elif prop_type == "select":
        return {"select": {"name": str(value)}}

    elif prop_type == "multi_select":
        if isinstance(value, str):
            value = [value]
        return {"multi_select": [{"name": str(v)} for v in value]}

    elif prop_type == "checkbox":
        return {"checkbox": bool(value)}

    elif prop_type == "date":
        return {"date": {"start": str(value)}}

    elif prop_type == "url":
        return {"url": str(value)}

    elif prop_type == "email":
        return {"email": str(value)}

    elif prop_type == "phone_number":
        return {"phone_number": str(value)}

    elif prop_type == "relation":
        if isinstance(value, str):
            value = [value]
        return {"relation": [{"id": v} for v in value]}

    return {"rich_text": [{"text": {"content": str(value)}}]}


# =============================================================================
# OPERATIONS (READ)
# =============================================================================


class GetCellOp(Operation[Any]):
    """Read operation for cell values."""

    def __init__(self, cell_ref: CellRef) -> None:
        self.cell_ref = cell_ref
        self.children = (cell_ref,)

    def execute(self, context: NotionContext) -> Any:
        resolved = self.cell_ref.resolve(context)
        page_id = resolved["page_id"]
        prop_name = resolved["property"]

        page_data = context.get_page(page_id)
        properties = page_data.get("properties", {})

        if prop_name not in properties:
            raise KeyError(f"Property '{prop_name}' not found in page")

        return extract_property_value(properties[prop_name])

    def __repr__(self) -> str:
        return f"GetCellOp({self.cell_ref!r})"


# =============================================================================
# COMMANDS (WRITE)
# =============================================================================


class AddRowCmd(Command[dict[str, Any]]):
    """Command to add a new row to a table."""

    def __init__(
        self,
        table_ref: TableRef,
        properties: dict[str, Any],
        table_shape: type | None = None,
    ) -> None:
        self.table_ref = table_ref
        self._properties = properties
        self._table_shape = table_shape
        self.children = (table_ref,)

    def execute(self, context: NotionContext) -> dict[str, Any]:
        resolved = self.table_ref.resolve(context)
        database_id = resolved["database_id"]

        # Resolve Term values
        properties = {}
        for key, value in self._properties.items():
            if isinstance(value, Term):
                value = value.execute(context)
            properties[key] = value

        # Convert to Notion format using slot info if available
        notion_properties = {}
        for key, value in properties.items():
            prop_type = None

            # Try to get type from shape slots
            if self._table_shape is not None:
                slots = getattr(self._table_shape, "_notion_slots", {})
                slot: NotionSlot | None = slots.get(key)
                if slot is not None:
                    prop_type = slot.notion_type

            notion_properties[key] = build_property_value(value, prop_type)

        return context.create_page(database_id, notion_properties)

    def __repr__(self) -> str:
        return f"AddRowCmd({self.table_ref!r}, ...)"


class RemoveRowCmd(Command[dict[str, Any]]):
    """Command to remove (archive) a row."""

    def __init__(self, row_ref: RowRef) -> None:
        self.row_ref = row_ref
        self.children = (row_ref,)

    def execute(self, context: NotionContext) -> dict[str, Any]:
        resolved = self.row_ref.resolve(context)
        return context.archive_page(resolved["page_id"])

    def __repr__(self) -> str:
        return f"RemoveRowCmd({self.row_ref!r})"


class SetCellCmd(Command[dict[str, Any]]):
    """Command to set a cell value."""

    def __init__(
        self,
        cell_ref: CellRef,
        value: Any | Term[Any],
        prop_type: str | None = None,
    ) -> None:
        self.cell_ref = cell_ref
        self._value = value
        self._prop_type = prop_type
        self.children = (cell_ref,)

    def execute(self, context: NotionContext) -> dict[str, Any]:
        resolved = self.cell_ref.resolve(context)
        page_id = resolved["page_id"]
        prop_name = resolved["property"]

        # Resolve value
        value = self._value
        if isinstance(value, Term):
            value = value.execute(context)

        # Infer prop_type from existing property if not set
        prop_type = self._prop_type
        if prop_type is None:
            try:
                page_data = context.get_page(page_id)
                existing_prop = page_data.get("properties", {}).get(prop_name, {})
                prop_type = existing_prop.get("type")
            except Exception:
                pass

        prop_value = build_property_value(value, prop_type)
        return context.update_page(page_id, {prop_name: prop_value})

    def __repr__(self) -> str:
        return f"SetCellCmd({self.cell_ref!r}, {self._value!r})"
