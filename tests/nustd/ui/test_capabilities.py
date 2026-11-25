"""Capabilities: the mixins, field reads, the session seams, and the rules every ref keeps.

The invariant walks every Ref class the kit ships and checks the rules the
capability mixins exist for:

- ``on_change`` only on a ``Readable``: a change can always be read back;
- every ``on_<x>()`` subscribes to the wire event ``x`` (``on_event()`` to
  every event);
- no ``get_*`` methods: reads are bare nouns;
- a named reader ``<x>()`` has its ``on_<x>()``, or the ``on_<event>()`` its
  ref names for it in ``_reader_events``.

``DERIVED`` names the few ``on_<x>()`` that are filters over a wire event
rather than an event of their own (History's ``on_path_change`` is ``change``
with the query and hash moves taken out). They are kept on purpose, not debt.

A ref that breaks one today sits in ``ALLOWLIST`` with the reason, one line
each. Fixing a ref means deleting its line: a line for a ref that keeps every
rule fails the test too, so the list only shrinks.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import pkgutil
from typing import ClassVar

import pytest

import nu
import nustd.ui as ui
from nu import Context, Shape
from nu.lang.literal import Literal
from nustd.ui import Column, Session
from nustd.ui.core import (
    ANY,
    CHANGE,
    EVENT,
    INPUT,
    OP_BATCH,
    OP_ERROR,
    OP_READ,
    OP_UNWATCH,
    OP_WATCH,
    SUBMIT,
    Changed,
    Changes,
    Emits,
    Frame,
    Moves,
    Readable,
    ReadField,
    Ref,
    Submits,
    WsSession,
    decode,
    encode,
    events,
)
from nustd.ui.core.interactions import _Only
from nustd.ui.refs import InputRef, Row, SelectRef, SliderRef, TextRef


# --- the allowlist -----------------------------------------------------------

#: Subscriptions that filter a wire event rather than name one, kept on purpose.
DERIVED: dict[str, str] = {
    "HistoryRef.on_path_change": "change, only the moves that touch the pathname",
}

#: Refs that break a rule, and why, one line each. Empty: a new ref keeps every rule.
ALLOWLIST: dict[str, str] = {}


# --- walking the kit ---------------------------------------------------------


def _shipped_refs() -> list[type[Ref]]:
    """Every public Ref class defined under ``nustd.ui``, each module imported first."""
    for mod in pkgutil.walk_packages(ui.__path__, "nustd.ui."):
        importlib.import_module(mod.name)
    seen: set[type] = set()
    todo: list[type] = [Ref]
    while todo:
        for sub in todo.pop().__subclasses__():
            if sub not in seen:
                seen.add(sub)
                todo.append(sub)
    return sorted(
        (
            c
            for c in seen
            if c.__module__.startswith("nustd.ui.") and not c.__name__.startswith("_")
        ),
        key=lambda c: c.__name__,
    )


def _public_methods(cls: type) -> list[str]:
    """Public plain methods on ``cls``, inherited ones included.

    Not the kernel's: the term surface every Nu node carries (``fallback``,
    ...) is not the ref's own.
    """
    names = []
    for name in dir(cls):
        if name.startswith("_"):
            continue
        owner = next(k for k in cls.__mro__ if name in vars(k))
        attr = vars(owner)[name]
        if not inspect.isfunction(attr) or owner.__module__.split(".")[0] == "nu":
            continue
        names.append(name)
    return names


def _takes_no_args(fn: object) -> bool:
    params = list(inspect.signature(fn).parameters.values())[1:]  # past self
    return all(
        p.default is not inspect.Parameter.empty
        or p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for p in params
    )


def _event_of(term: Changed) -> str | None:
    """The one event a ``Changed`` subscribes to, None for every event."""
    if len(term._children) < 2:
        return None
    event = term._children[1]
    return event.value if isinstance(event, Literal) else repr(event)


def _violations(cls: type[Ref]) -> list[str]:
    """Which rules ``cls`` breaks, one short line each; empty when it keeps them all."""
    found: list[str] = []
    methods = _public_methods(cls)
    if "on_change" in methods and not issubclass(cls, Readable):
        found.append("on_change on a ref that is not Readable")
    found.extend(f"{name}: no get_ methods" for name in methods if name.startswith("get_"))

    ref = cls("probe")
    readers: list[str] = []
    for name in methods:
        fn = getattr(cls, name)
        if not _takes_no_args(fn):
            continue
        if name.startswith("on_"):
            if f"{cls.__name__}.{name}" in DERIVED:
                continue
            term = getattr(ref, name)()
            if not isinstance(term, Changed):
                found.append(f"{name}: returns {type(term).__name__}, not Changed")
                continue
            want = None if name == "on_event" else name.removeprefix("on_")
            got = _event_of(term)
            if got != want:
                found.append(f"{name}: subscribes to {got!r}, not {want!r}")
        elif issubclass(cls, Readable) and name != "set" and not name.startswith("set_"):
            # a named reader is ``self._read(...)``, which only a Readable has
            term = getattr(ref, name)()
            if isinstance(term, ReadField):
                readers.append(term._children[1].value)
    events = getattr(cls, "_reader_events", {})
    for field in readers:
        event = events.get(field, field)
        if f"on_{event}" not in methods:
            found.append(f"{field}(): no on_{event}()")
    return found


def test_the_walk_finds_the_kit():
    names = {c.__name__ for c in _shipped_refs()}
    assert {"InputRef", "SliderRef", "TabsRef", "TreeRef", "DataTableRef", "ButtonRef"} <= names
    assert "LensRef" in names  # behind nustd.ui.lens, still walked


def test_every_ref_keeps_the_rules_or_is_allowlisted():
    broken = {c.__name__: _violations(c) for c in _shipped_refs()}
    broken = {name: why for name, why in broken.items() if why}
    unlisted = {name: why for name, why in broken.items() if name not in ALLOWLIST}
    assert not unlisted, f"refs breaking the rules, not allowlisted: {unlisted}"


def test_the_allowlist_has_no_stale_lines():
    kept = {c.__name__ for c in _shipped_refs() if not _violations(c)}
    stale = sorted(kept & set(ALLOWLIST))
    assert not stale, f"these refs keep every rule now, delete their ALLOWLIST lines: {stale}"
    names = {c.__name__ for c in _shipped_refs()}
    assert set(ALLOWLIST) <= names, f"allowlisted refs that do not exist: {set(ALLOWLIST) - names}"


# --- the mixins --------------------------------------------------------------


def test_event_names_are_the_wire_names():
    assert (EVENT, ANY, INPUT, CHANGE, SUBMIT) == ("event", "*", "input", "change", "submit")
    assert events.ROW_CLICK == "row_click"


def test_the_old_import_sites_still_resolve():
    from nustd.ui.core import interactions
    from nustd.ui.refs.leaves import input as input_leaves

    assert interactions.EVENT == EVENT
    assert input_leaves.CHANGE == CHANGE


def test_changes_is_readable_and_emits():
    assert issubclass(Changes, Readable)
    assert issubclass(Changes, Emits)
    assert issubclass(Moves, Emits)
    assert issubclass(Submits, Emits)


def test_every_input_is_readable_and_changes():
    assert issubclass(SliderRef, Changes)
    assert issubclass(InputRef, Submits)
    assert not issubclass(SliderRef, Submits)


def test_on_event_hears_every_event():
    term = SliderRef("s").on_event()
    assert isinstance(term, Changed)
    assert _event_of(term) is None


def test_on_change_and_on_submit_name_their_event():
    ref = InputRef("q")
    assert _event_of(ref.on_change()) == CHANGE
    assert _event_of(ref.on_submit()) == SUBMIT


def test_on_input_names_input():
    assert _event_of(InputRef("q").on_input()) == INPUT


def test_mixins_and_events_reach_the_public_surface():
    for name in (
        "Emits",
        "Readable",
        "Changes",
        "Moves",
        "Submits",
        "ReadField",
        "EVENT",
        "CHANGE",
    ):
        assert hasattr(ui, name), name


# --- reads and subscriptions over a fake session -----------------------------


class _Tab:
    """Fake session: records reads (path, field) and subscriptions (path, event)."""

    def __init__(self, answers: dict | None = None) -> None:
        self.answers = answers or {}
        self.reads: list[tuple[tuple[str, ...], str | None]] = []
        self.subscribed: list[tuple[tuple[str, ...], str | None]] = []

    async def send(self, frame: object) -> None:
        pass

    async def aread(self, path: tuple[str, ...], field: str | None = None) -> object:
        self.reads.append((path, field))
        return self.answers.get(field)

    def subscribe(self, path: tuple[str, ...], event: str | None = None) -> _Sub:
        self.subscribed.append((path, event))
        return _Sub()


class _Sub:
    def bind(self, cb):
        pass

    def unbind(self, cb):
        pass

    def close(self):
        pass


def _mount(widget_slot):
    sec = type("CSec", (Row,), {"w": widget_slot})
    page = type("CPage", (Column,), {"sec": sec.slot()})
    app = type("CApp", (Shape,), {"page": page.slot()})
    return app.page.sec.w


def _run(term, tab: _Tab) -> object:
    value, _ = asyncio.run(nu.arun(term, Context().bind(Session, tab)))
    return value


class _Spinner(SelectRef):
    """A ref with a named reader, the way a family adds one."""

    def options_open(self) -> ReadField:
        return self._read("options_open")

    def _lift_field(self, field: str, raw: object) -> object:
        return bool(raw)


def test_the_main_read_sends_no_field():
    ref = _mount(InputRef.slot())
    tab = _Tab({None: "hi"})
    assert _run(ref, tab) == "hi"
    assert tab.reads == [(("page", "sec", "w"), None)]


def test_a_named_reader_reads_its_field_once():
    ref = _mount(_Spinner.slot(options=["a"]))
    tab = _Tab({"options_open": 1})
    assert _run(ref.options_open(), tab) is True  # through _lift_field
    assert tab.reads == [(("page", "sec", "w"), "options_open")]


def test_a_reader_without_its_event_is_a_violation():
    assert _violations(_Spinner) == ["options_open(): no on_options_open()"]


class _Folding(_Spinner):
    """A reader whose field moves on an event named otherwise."""

    _reader_events: ClassVar[dict[str, str]] = {"options_open": "toggle"}

    def on_toggle(self) -> Changed:
        return Changed(self, "toggle")


def test_a_reader_may_name_its_event():
    assert _violations(_Folding) == []


def test_changed_hands_its_event_to_the_session():
    ref = _mount(InputRef.slot())
    tab = _Tab()
    sub = _run(ref.on_change(), tab)
    assert isinstance(sub, _Only)
    _run(ref.on_event(), tab)
    assert tab.subscribed == [(("page", "sec", "w"), CHANGE), (("page", "sec", "w"), None)]


# --- the ws session and the protocol -----------------------------------------


class _Ws:
    def __init__(self) -> None:
        self.sent: list[bytes] = []

    async def send_bytes(self, raw: bytes) -> None:
        self.sent.append(raw)


def test_ws_read_frame_payload_is_field_or_null():
    ws = _Ws()
    session = WsSession(ws)  # type: ignore[arg-type]

    async def run():
        for field in (None, "expanded"):
            task = asyncio.create_task(session.aread(("t",), field))
            while not session._pending:
                await asyncio.sleep(0)
            [rid] = session._pending
            session._dispatch(decode(encode(Frame(OP_READ, ref=("t",), payload=field, id=rid))))
            assert await task == field

    asyncio.run(run())
    payloads = [decode(raw).payload for raw in ws.sent]
    assert payloads == [None, {"field": "expanded"}]


def test_ws_read_of_a_field_the_node_lacks_raises():
    session = WsSession(_Ws())  # type: ignore[arg-type]
    refusal = {"code": "payload_invalid", "message": 'TreeRef has no read "nope"'}

    async def run():
        task = asyncio.create_task(session.aread(("t",), "nope"))
        while not session._pending:
            await asyncio.sleep(0)
        [rid] = session._pending
        session._dispatch(decode(encode(Frame(OP_ERROR, ref=("t",), payload=refusal, id=rid))))
        with pytest.raises(LookupError, match="payload_invalid at t"):
            await task

    asyncio.run(run())


def test_ws_subscribe_takes_an_event():
    session = WsSession(_Ws())  # type: ignore[arg-type]
    sub = session.subscribe(("t",), event=CHANGE)
    seen: list = []
    sub.bind(seen.append)
    session._dispatch(Frame("notify", ref=("t",), payload={EVENT: INPUT}))
    assert seen == [{EVENT: INPUT}]  # no watch behavior yet: the filter is Changed's


def test_new_ops_are_named():
    assert (OP_WATCH, OP_UNWATCH, OP_BATCH) == ("watch", "unwatch", "batch")


def test_text_is_not_readable():
    """Server-written state is not read back: Text has no main read."""
    assert not issubclass(TextRef, Readable)
