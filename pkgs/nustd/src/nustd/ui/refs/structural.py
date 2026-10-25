"""Structural Refs -- bound to non-render browser APIs.

Index-level Refs whose side effects live on the platform (window.history,
document.title), not the visible body tree. Leaves: neither draws anything
in the body, and neither holds children.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Changed, Write

from .leaves.base import LeafRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import StrArg
    from nu.lang.runtime import Runtime


__all__ = ["NavRef", "TitleRef"]


class NavRef(LeafRef):
    """Bound to the page's location. Index-level structural Ref.

    Bidirectional: host writes move the page; a move the host did not ask
    for (back/forward, or a route change under a host router) ships a
    `notify` whose payload is the new URI.

    The browser moves through its active navigator: plain window.history by
    default, or the router of a host that installed its own (the kit's
    ``setNavigator``), so a write moves whatever that host draws.

    API for host code:
        nav.set(uri)            -- push a new URI onto history
        nav.replace(uri)        -- replace the current entry (no back-stack growth)
        nav.back()              -- history.back()
        nav.forward()           -- history.forward()
        nav.on_change()         -- subscribe to user navigation events
        await nav.aread(...)    -- through session, fetch current URI

    All four host writes compile to the `write` op. `set(uri)` ships a bare
    string; the other three ship a tagged dict the browser slice dispatches on.
    """

    _wire_type = "NavRef"

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        # Bare-string push -- shorthand for {"action": "push", "uri": value}.
        return Write(self, value)

    def replace(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(action="replace", uri=value))

    def back(self) -> Nu:
        return Write(self, Dict.of(action="back"))

    def forward(self) -> Nu:
        return Write(self, Dict.of(action="forward"))

    def on_change(self) -> Changed:
        return Changed(self)


class TitleRef(LeafRef):
    """Bound to document.title. Index-level structural Ref.

    Write-only from host. The browser-side slice writes assignments
    directly to document.title; it is not a body slot and is not
    rendered into the visible tree. Slot-level `default` and `suffix`
    seed the browser on init.
    """

    _wire_type = "TitleRef"

    @classmethod
    def slot(cls, *, default: str = "", suffix: str = "") -> Self:
        return super().slot(default=default, suffix=suffix)

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)
