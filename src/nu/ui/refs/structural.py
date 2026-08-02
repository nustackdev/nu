"""Structural Refs -- bound to non-render browser APIs.

Index-level Refs whose side effects live on the platform (window.history,
document.title), not the visible body tree. See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from nu import Dict
from nu.ui.core import Changed, Ref, Write


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.args import StrArg
    from nu.lang.runtime import Runtime


__all__ = ["NavRef", "TitleRef"]


class NavRef(Ref):
    """Bound to window.history + window.location. Index-level structural Ref.

    Bidirectional: host writes manipulate window.history; user navigation
    (link clicks, back/forward) ships a `notify` whose payload is the new URI.

    API for host code:
        nav.set(uri)              -- push a new URI onto history
        nav.replace(uri)            -- replace the current entry (no back-stack growth)
        nav.back()                  -- history.back()
        nav.forward()               -- history.forward()
        nav.changed()               -- subscribe to user navigation events
        await nav.aread(...)        -- through session, fetch current URI

    All four host writes compile to the existing `write` op. `set(uri)`
    ships a bare string for back-compat; the other three ship a tagged
    dict the browser slice dispatches on.
    """

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        # Bare-string push -- shorthand for {"action": "push", "uri": value}.
        # Kept as bare-string to preserve existing host code (multipage.py).
        return Write(self, value)

    def replace(self, value: StrArg) -> Nu:
        return Write(self, Dict.of(action="replace", uri=value))

    def back(self) -> Nu:
        return Write(self, Dict.of(action="back"))

    def forward(self) -> Nu:
        return Write(self, Dict.of(action="forward"))

    def changed(self) -> Changed:
        return Changed(self)


class TitleRef(Ref):
    """Bound to document.title. Index-level structural Ref.

    Write-only from host. The browser-side slice writes assignments
    directly to document.title; it is not a body slot and is not
    rendered into the visible tree. Slot-level `default` and `suffix`
    seed the browser on mount.
    """

    @classmethod
    def slot(cls, *, default: str = "", suffix: str = "") -> Self:
        return super().slot(default=default, suffix=suffix)

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)
