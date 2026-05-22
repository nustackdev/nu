"""NavRef: structural Ref bound to the browser's history + location.

Lives on an Index. Bidirectional: host writes push a new entry into
window.history; user navigation (link clicks, back/forward) ships a
`notify` whose payload is the new URI.

API for host code:
    nav.store("/feed")          -- push a new URI onto history
    nav.changed()               -- subscribe to user navigation events
    await nav.aread(...)        -- through session, fetch current URI

Underneath this is just `Write` (push) + `Changed` (popstate) + a `read`
round-trip. The browser-side factory binds these ops to window.history,
window.location, and popstate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["NavRef"]


class NavRef(NudleRef):
    """Bound to window.history + window.location. Index-level structural Ref."""

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)
