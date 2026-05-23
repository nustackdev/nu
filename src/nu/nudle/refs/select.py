"""SelectRef: single-select dropdown over a fixed list of options. Browser is the source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.queries.record import Record

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["SelectRef"]


OptionInput = "list[str] | list[dict[str, str]]"


def _normalize_options(opts: object) -> list[dict[str, str]]:
    """Accept ["a", "b"] or [{"value": "a", "label": "A"}] and return the dict form."""
    if not isinstance(opts, list):
        return []
    out: list[dict[str, str]] = []
    for item in opts:
        if isinstance(item, str):
            out.append({"value": item, "label": item})
        elif isinstance(item, dict):
            value = str(item.get("value", "")) if item.get("value") is not None else ""
            label = str(item.get("label", value)) if item.get("label") is not None else value
            out.append({"value": value, "label": label})
    return out


class SelectRef(NudleRef):
    """Dropdown single-select whose value lives in the browser."""

    options: ClassVar[list[Any]] = []
    selected: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "options": _normalize_options(cls.options),
            "selected": cls.selected,
            "placeholder": cls.placeholder,
        }

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def store_options(self, opts: Nu | list[str] | list[dict[str, str]]) -> Nu:
        if isinstance(opts, list):
            payload: object = {"options": _normalize_options(opts)}
        else:
            payload = {"options": opts}
        return Write(self, Record(**payload))

    def changed(self) -> Changed:
        return Changed(self)
