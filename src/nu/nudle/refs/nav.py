"""NavRef: structural Ref bound to the browser's history + location.

Lives on an Index. Bidirectional: host writes manipulate
window.history; user navigation (link clicks, back/forward) ships a
`notify` whose payload is the new URI.

API for host code:
    nav.store(uri)              -- push a new URI onto history
    nav.replace(uri)            -- replace the current entry (no back-stack growth)
    nav.back()                  -- history.back()
    nav.forward()               -- history.forward()
    nav.changed()               -- subscribe to user navigation events
    await nav.aread(...)        -- through session, fetch current URI

All four host writes compile to the existing `write` op. `store(uri)`
ships a bare string for back-compat; the other three ship a tagged dict
the browser slice dispatches on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.queries.record import Record

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
        # Bare-string push -- shorthand for {"action": "push", "uri": value}.
        # Kept as bare-string to preserve existing host code (multipage.py).
        return Write(self, value)

    def replace(self, value: Nu | str) -> Nu:
        return Write(self, Record(action="replace", uri=value))

    def back(self) -> Nu:
        return Write(self, Record(action="back"))

    def forward(self) -> Nu:
        return Write(self, Record(action="forward"))

    def changed(self) -> Changed:
        return Changed(self)
