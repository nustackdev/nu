"""nudle Ref types for v0.1.0.

Each Ref carries a `wire_type` class var; that string lands in the `mount`
frame and is the key the browser uses to pick a renderer. The Ref overrides
`.store()` / `.append()` to emit nudle commands.

For v0.1.0 pages are flat (no nested Shapes), so a Ref's address is its
field name and `aresolve` returns that string directly. When nested pages
land, this widens to dot-joined paths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from nu.shapes.refs import Ref
from nu.shapes.shape.slot import Slot
from nu.terms.types import Mode

from .commands import NudleAppendCmd, NudleWriteCmd


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = [
    "IntRef",
    "LineChart",
    "NudleRef",
    "TitleRef",
]


_ASYNC = frozenset({Mode.ASYNC})


class NudleRef(Ref[Any]):
    """Base for refs whose state lives in a browser tab over ws."""

    support: ClassVar[frozenset[Mode]] = _ASYNC
    wire_type: ClassVar[str] = ""

    async def afetch_parent(self, ctx: Context) -> object:
        # Commands resolve the session directly; parent is not used in v0.1.0.
        raise NotImplementedError("nudle refs do not expose a parent view")

    async def aresolve(self, ctx: Context) -> str:
        return await self.aresolve_address(ctx)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]


class TitleRef(NudleRef):
    """Page title or section heading. Renders as <h1>."""

    wire_type: ClassVar[str] = "TitleRef"

    def store(self, value: Nu | str) -> Nu:
        return NudleWriteCmd(self, value)


class IntRef(NudleRef):
    """Integer cell. Renders as <span>."""

    wire_type: ClassVar[str] = "IntRef"

    def store(self, value: Nu | int) -> Nu:
        return NudleWriteCmd(self, value)


class LineChart(NudleRef):
    """Time-series line chart. Renders as a recharts LineChart."""

    wire_type: ClassVar[str] = "LineChart"

    def store(self, value: Nu | dict) -> Nu:
        return NudleWriteCmd(self, value)

    def append(self, x: Nu | float, y: Nu | float) -> Nu:
        return NudleAppendCmd(self, x, y)
