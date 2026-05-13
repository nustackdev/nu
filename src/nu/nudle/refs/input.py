"""InputRef: text input. Browser is the source of truth.

Using `InputRef` in a query position (e.g. inside an expression) issues
a `read` round-trip to the tab and resolves to the current local value.
`InputRef.changed()` returns a Subscription that fires whenever the user
commits a change in the browser (blur or Enter, see web/src/refs/input.tsx).

`store(value)` is supported so the server can push a value back into the
input -- canonical or reset semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["InputRef"]


class InputRef(NudleRef):
    """Text input whose value lives in the browser."""

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
