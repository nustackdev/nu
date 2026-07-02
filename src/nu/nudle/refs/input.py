"""InputRef: text input. Browser is the source of truth.

Using `InputRef` in a query position (e.g. inside an expression) issues
a `read` round-trip to the tab and resolves to the current local value.
`InputRef.changed()` returns a Subscription that fires whenever the user
commits a change in the browser (blur or Enter, see web/src/refs/input.tsx).

`store(value)` is supported so the server can push a value back into the
input -- canonical or reset semantics.

Class-level defaults (`label`, `placeholder`, `value`, `type`, `max_length`)
are shipped on `mount` under the field entry's `props` key and seed the
browser slice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["InputRef"]


InputType = Literal["text", "password", "email", "number"]


class InputRef(NudleRef):
    """Text input whose value lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    value: ClassVar[str] = ""
    type: ClassVar[str] = "text"
    max_length: ClassVar[int | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "value": cls.value,
            "type": cls.type,
            "max_length": cls.max_length,
        }

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
