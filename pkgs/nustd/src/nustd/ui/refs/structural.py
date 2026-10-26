"""Structural Refs -- bound to non-render browser APIs.

Index-level Refs whose side effects live on the platform (the page's
History, document.title), not the visible body tree. Leaves: neither draws
anything in the body, and neither holds children. ``NavRef`` is
``HistoryRef``'s old name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.engine.structure import Declared
from nu.forms import Dict
from nu.lang import ScalarQuery
from nu.lang.sentinels import UNSET
from nustd.ui.core import Changed, Session, Write

from .leaves.base import LeafRef
from .query import decode_query


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.lang import Nu
    from nu.lang.args import StrArg
    from nu.lang.runtime import Runtime


__all__ = ["HistoryRef", "NavRef", "TitleRef"]


def _entry_of(raw: object) -> dict[str, Any]:
    """The browser's read as an entry dict, whichever kit answered it.

    The kit answers with the whole entry; one from before HistoryRef answered
    with the bare uri, which is read here as an entry with no state.
    """
    if isinstance(raw, dict):
        uri = str(raw.get("uri") or "/")
        query = raw.get("query")
        return {
            "uri": uri,
            "path": str(raw.get("path") or uri.split("?", 1)[0].split("#", 1)[0]),
            "query": dict(query) if isinstance(query, dict) else {},
            "hash": str(raw.get("hash") or ""),
            "state": raw.get("state"),
        }
    uri = "/" if raw is None else str(raw)
    rest, _, fragment = uri.partition("#")
    path, _, search = rest.partition("?")
    return {
        "uri": uri,
        "path": path or "/",
        "query": decode_query(search),
        "hash": f"#{fragment}" if fragment else "",
        "state": None,
    }


class ReadEntry(ScalarQuery):
    """Read the page's History entry through a HistoryRef: one round trip.

    Yields the whole entry, ``{"uri", "path", "query", "hash", "state"}``, or
    the one field named by ``field``. Resolves the Ref's wire path but never
    evals the Ref child, so it reads once, not twice.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: HistoryRef, field: StrArg | None = None) -> None:
        if field is None:
            super().__init__(ref)
        else:
            super().__init__(ref, field)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Any:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: HistoryRef = self._children[0]
        field_thunk = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> Any:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            entry = _entry_of(await session.aread(path))
            if field_thunk is None:
                return entry
            return entry[str(await field_thunk(rt))]

        return athunk


class HistoryRef(LeafRef):
    """The page's History: where it is, and the server's way to move it.

    Index-level structural Ref, drawn as nothing. The browser keeps one stack
    of entries, each a URL plus state, a data value that rides with the entry
    and is not in the URL. Every move goes through the kit's History.

    Moves (all compile to the ``write`` op):
        nav.push(uri, state=)   -- a new entry; ``set(uri)`` is the same
        nav.replace(uri, state=) -- in place of the current entry
        nav.back() / nav.forward()
        nav.set_query(**kv)     -- the current query with ``kv`` merged in,
                                   None dropping a key, as a replace: a filter
                                   typed into never floods back

    Reads (each one round trip):
        nav                     -- the uri, path, query and hash: "/feed?x=1"
        nav.entry()             -- {"uri", "path", "query", "hash", "state"}
        nav.query()             -- the query as a dict of strings
        nav.state()             -- the entry's state, None for none
        nav.path()              -- the pathname alone

    ``nav.on_change()`` hears every move the page makes except the ones this
    ref's own moves caused: the user's back button, a link the host routed,
    another HistoryRef's push. The payload is the new uri.

    State must be what the browser can structured-clone: dicts, lists,
    strings, numbers, booleans and None. The query encoding is the one
    ``encode_query`` writes (``nustd.ui``), the same on both sides.
    """

    _wire_type = "HistoryRef"

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def _lift(self, raw: object) -> object:
        # Reading the ref is the uri, as it always was; the rest of the entry
        # is ``entry()``.
        return _entry_of(raw)["uri"]

    # --- moves ---------------------------------------------------------------

    def push(self, uri: StrArg, state: object = UNSET) -> Nu:
        """Go to ``uri``, a new entry, carrying ``state`` when given."""
        return Write(self, self._move("push", uri, state))

    def set(self, uri: StrArg, state: object = UNSET) -> Nu:
        """``push``, under the name every Ref's primary write has."""
        return self.push(uri, state)

    def replace(self, uri: StrArg, state: object = UNSET) -> Nu:
        """Go to ``uri`` in place of the current entry: the back stack does not grow."""
        return Write(self, self._move("replace", uri, state))

    def back(self) -> Nu:
        return Write(self, Dict.of(action="back"))

    def forward(self) -> Nu:
        return Write(self, Dict.of(action="forward"))

    def set_query(self, values: Mapping[str, object] | None = None, /, **kv: object) -> Nu:
        """Merge ``values`` and ``kv`` into the current query, as a replace.

        A None value drops its key; the path, hash and state stay. Keys that
        are no Python name go in ``values``: ``nav.set_query({"sort-by": "date"})``.
        """
        merged = {**(values or {}), **kv}
        return Write(self, Dict.of(action="set_query", query=Dict.of(**merged)))

    @staticmethod
    def _move(action: str, uri: StrArg, state: object) -> Nu:
        if state is UNSET:
            return Dict.of(action=action, uri=uri)
        return Dict.of(action=action, uri=uri, state=state)

    # --- reads ---------------------------------------------------------------

    def entry(self) -> ReadEntry:
        """The whole entry: ``{"uri", "path", "query", "hash", "state"}``."""
        return ReadEntry(self)

    def query(self) -> ReadEntry:
        """The current query as a dict of strings."""
        return ReadEntry(self, "query")

    def state(self) -> ReadEntry:
        """The current entry's state, None for none."""
        return ReadEntry(self, "state")

    def path(self) -> ReadEntry:
        """The current pathname, no query or hash."""
        return ReadEntry(self, "path")

    def on_change(self) -> Changed:
        return Changed(self)


#: The old name of ``HistoryRef``, kept so programs written against it run as
#: they did. Same class, same wire type.
NavRef = HistoryRef


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
