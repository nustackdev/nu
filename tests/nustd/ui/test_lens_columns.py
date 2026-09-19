"""What a cursor is worth as columns, over a Shape built for the purpose.

Writes happen in the fixture and a navigation is a read, which is the shape a
live lens has. Nothing here goes near a browser: the wire shape is the whole
subject, and a Shape with one of every kind of slot is what makes the sequence
column, the mapping-of-values column, the cap and the sentinels show
themselves.

``Zoo`` is mounted twice, which is the other half of the subject: one Shape
reading different data depending on the ref it was anchored at.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nustd.kv
import nustd.ui
from nustd.ui.lens import column_terms
from nustd.ui.lens.presets import _nav_key
from virtuals import Navigator


class Keeper(nu.Shape):
    """Something for the two shapes-containers to hold."""

    name = nustd.kv.StrRef.slot()


class Zoo(nu.Shape):
    """One of each kind of slot, which is the whole point of it."""

    title = nustd.kv.StrRef.slot()
    unset = nustd.kv.StrRef.slot()
    tags = nustd.kv.ListRef.slot(str)
    counts = nustd.kv.DictRef.slot(int)
    loose = nustd.kv.DictRef.slot(object)
    keepers = nustd.kv.ShapesDictRef.slot(Keeper)
    shifts = nustd.kv.ShapesListRef.slot(Keeper)


class Store(nu.Shape):
    """Two anchors for one Zoo, so a prefix has something to choose between."""

    left = nustd.kv.ShapeRef.slot(Zoo)
    right = nustd.kv.ShapeRef.slot(Zoo)


def _seed() -> nu.Nu:
    """One full Zoo on the left, a thinner one on the right."""
    return (
        Store.left.title.set(nu.Str("a zoo"))
        | Store.left.tags.init(nu.List.create())
        | Store.left.counts.init(nu.Dict.create())
        | Store.left.loose.init(nu.Dict.create())
        | Store.left.shifts.init(nu.List.create())
        | Store.right.title.set(nu.Str("the other zoo"))
        | Store.right.tags.init(nu.List.create())
    ) >> (
        Store.left.tags.append(nu.Str("red"))
        >> Store.left.tags.append(nu.Str("blue"))
        >> Store.left.tags.append(nu.Str("green"))
        >> Store.left.counts.set_item(nu.Str("red"), nu.Int(3))
        >> Store.left.counts.set_item(nu.Str("blue"), nu.Int(0))
        >> Store.left.loose.set_item(nu.Str("whatever"), nu.Str("nobody declared this"))
        >> Store.left.loose.set_item(nu.Str("and_this"), nu.Int(7))
        >> Store.left.keepers["ada"].name.set(nu.Str("Ada"))
        >> Store.left.shifts.append(nu.Dict.of(name=nu.Str("dawn")))
    )


@pytest.fixture
async def store():
    """One in-memory store with the zoos in it, gone when the test ends."""
    with nustd.kv.memory_storage() as storage:
        ctx = nu.Context().bind(Navigator, Navigator(storage))
        await nu.arun(nustd.kv.Transaction(_seed()), ctx)
        yield ctx


async def _read(ctx: nu.Context, term: nu.Nu) -> list:
    """Run ``term`` against the seeded store, in a snapshot."""
    cols, _ = await nu.arun(nustd.kv.Snapshot(term), ctx)
    return cols


async def _at(ctx: nu.Context, cursor, prefix=Store.left, max_rows=200) -> list:
    """The cascade for ``cursor``, built in python. The common case."""
    return await _read(ctx, column_terms(Zoo, cursor, prefix=prefix, max_rows=max_rows))


@pytest.mark.timeout(60)
async def test_the_root_column_is_the_shape_and_its_leaf_values(store):
    """Slots are schema; a leaf slot also carries what the store has."""
    (root,) = await _at(store, ())
    assert root["kind"] == "shape"
    assert root["total"] == 7
    rows = {e["key"]: e for e in root["entries"]}
    assert [e["kind"] for e in root["entries"]] == [
        "leaf",
        "leaf",
        "sequence",
        "mapping",
        "mapping",
        "mapping",
        "sequence",
    ]
    assert rows["title"]["preview"] == "a zoo"
    assert rows["title"]["vtype"] == "str"
    # A slot nobody ever wrote reads as the sentinel it is, not as "".
    assert rows["unset"]["vtype"] == "empty"
    assert rows["unset"]["preview"] == ""
    # A structured slot is a door. It says which kind of column it opens and
    # touches the store for nothing.
    assert rows["tags"]["preview"] == ""
    assert all(e["navigable"] for e in root["entries"])


@pytest.mark.timeout(60)
async def test_a_sequence_column_is_positions_and_values(store):
    cols = await _at(store, ("tags",))
    assert len(cols) == 2
    col = cols[1]
    assert col["kind"] == "sequence"
    assert col["total"] == 3
    assert [e["key"] for e in col["entries"]] == ["0", "1", "2"]
    assert [e["preview"] for e in col["entries"]] == ["red", "blue", "green"]
    # A position holds a value, and there is nothing under it to open.
    assert not any(e["navigable"] for e in col["entries"])


@pytest.mark.timeout(60)
async def test_a_mapping_of_values_shows_the_values(store):
    """A dict of ints is not a dict of Shapes, and the column says so."""
    col = (await _at(store, ("counts",)))[1]
    assert col["kind"] == "mapping"
    assert col["total"] == 2
    rows = {e["key"]: e for e in col["entries"]}
    assert rows["red"]["preview"] == "3"
    assert rows["red"]["vtype"] == "int"
    # Zero is a value. It must not read as empty, or every falsy leaf in the
    # store would look unwritten.
    assert rows["blue"]["preview"] == "0"
    assert rows["blue"]["vtype"] == "int"


@pytest.mark.timeout(60)
async def test_a_declared_container_shows_what_a_program_put_in_it(store):
    """The shape supplies the protocol; kv supplies the contents.

    ``loose`` declares a mapping and says nothing about its keys, so the column
    is exactly what was written, of whatever types were written.
    """
    col = (await _at(store, ("loose",)))[1]
    assert col["kind"] == "mapping"
    rows = {e["key"]: e for e in col["entries"]}
    assert rows["whatever"]["preview"] == "nobody declared this"
    assert rows["whatever"]["vtype"] == "str"
    assert rows["and_this"]["vtype"] == "int"


@pytest.mark.timeout(60)
async def test_a_container_of_shapes_offers_ways_in_and_reads_nothing(store):
    """A key onto a Shape is a door, whether it is named or positional."""
    keepers = (await _at(store, ("keepers",)))[1]
    assert keepers["kind"] == "mapping"
    assert [(e["key"], e["kind"], e["navigable"]) for e in keepers["entries"]] == [
        ("ada", "shape", True)
    ]
    assert keepers["entries"][0]["preview"] == ""

    shifts = (await _at(store, ("shifts",)))[1]
    assert shifts["kind"] == "sequence"
    assert [(e["key"], e["kind"], e["navigable"]) for e in shifts["entries"]] == [
        ("0", "shape", True)
    ]

    # And each door opens on the Shape behind it, not on a repr of one.
    assert (await _at(store, ("keepers", "ada")))[-1]["entries"][0]["preview"] == "Ada"
    assert (await _at(store, ("shifts", "0")))[-1]["entries"][0]["preview"] == "dawn"


@pytest.mark.timeout(60)
async def test_a_position_that_is_not_a_position_is_an_error_column(store):
    """A position is an int and a wire segment is a string, so the cast is the check."""
    cols = await _at(store, ("tags", "red"))
    assert len(cols) == 3
    assert cols[2]["entries"][0]["vtype"] == "error"


@pytest.mark.timeout(60)
async def test_a_leaf_column_carries_the_whole_value(store):
    cols = await _at(store, ("title",))
    assert len(cols) == 2
    (cell,) = cols[1]["entries"]
    assert cols[1]["kind"] == "leaf"
    assert cell["text"] == "a zoo"
    assert cell["clipped"] is False
    assert cell["navigable"] is False


@pytest.mark.timeout(60)
async def test_the_cap_clips_the_rows_and_keeps_the_total(store):
    """``max_rows`` is a hard cap with no pagination, and the total says so."""
    for cursor in (("tags",), ("counts",)):
        col = (await _at(store, cursor, max_rows=1))[1]
        assert len(col["entries"]) == 1
        assert col["total"] > 1


@pytest.mark.timeout(60)
async def test_a_segment_that_names_nothing_is_one_error_column(store):
    """Total by construction: a bad crumb costs its own column and no more."""
    cols = await _at(store, ("title", "nope"))
    assert len(cols) == 3
    assert cols[0]["kind"] == "shape"
    assert cols[2]["entries"][0]["vtype"] == "error"


@pytest.mark.timeout(60)
async def test_a_cursor_the_browser_sent_drives_the_same_walk(store):
    """The cursor as a runtime value, which is the only way it ever arrives."""
    cols = await _read(
        store, nustd.ui.lens.columns(Zoo, nu.List.of(nu.Str("tags")), prefix=Store.left, max_rows=2)
    )
    assert len(cols) == 2
    assert cols[1]["kind"] == "sequence"
    assert [e["key"] for e in cols[1]["entries"]] == ["0", "1"]
    assert cols[1]["total"] == 3


@pytest.mark.timeout(60)
async def test_a_read_that_fails_at_run_still_answers_with_a_cascade():
    """A frame always comes back, or the browser waits on one forever.

    No store bound at all, which is the whole class of failure the walk cannot
    see coming: it builds a perfectly good term and the reads die later. Every
    cursor a browser can spell is caught while the term is built, so this guard
    is for what goes wrong underneath rather than for what was asked.
    """
    cols, _ = await nu.arun(
        nustd.ui.lens.columns(Zoo, nu.List.of(nu.Str("counts")), prefix=Store.left), nu.Context()
    )
    assert cols[-1]["entries"][0]["vtype"] == "error"


# --- the prefix -------------------------------------------------------------


@pytest.mark.timeout(60)
async def test_one_shape_at_two_anchors_reads_two_different_things(store):
    """The Shape says what to expect; the prefix says whose."""
    left = (await _at(store, (), prefix=Store.left))[0]
    right = (await _at(store, (), prefix=Store.right))[0]
    assert {e["key"] for e in left["entries"]} == {e["key"] for e in right["entries"]}
    assert next(e for e in left["entries"] if e["key"] == "title")["preview"] == "a zoo"
    assert next(e for e in right["entries"] if e["key"] == "title")["preview"] == "the other zoo"
    # The right one was never given tags, so its sequence slot is its own and
    # empty rather than the left one's.
    assert (await _at(store, ("tags",), prefix=Store.right))[1]["total"] == 0


@pytest.mark.timeout(60)
async def test_no_prefix_reads_the_shape_at_the_root_of_its_own_store(store):
    """A bare Shape class already names a location, and nothing was written there."""
    root = (await _at(store, (), prefix=None))[0]
    assert root["kind"] == "shape"
    assert next(e for e in root["entries"] if e["key"] == "title")["vtype"] == "empty"


@pytest.mark.timeout(60)
async def test_a_cursor_cannot_name_anything_above_the_prefix(store):
    """Containment, and it is structural rather than a check.

    There is no path string to escape from: segment one is a slot name on the
    Shape or it is nothing, so every spelling of "go up" is the same error
    column, with the column to its left untouched.
    """
    for climb in ("..", "/", "left", "__parent__", ""):
        cols = await _at(store, (climb,))
        assert len(cols) == 2
        assert cols[0]["kind"] == "shape"
        assert cols[1]["entries"][0]["vtype"] == "error"


# --- the wire, and the assembled preset -------------------------------------


class Panel(nustd.ui.Card):
    lens = nustd.ui.lens.LensRef.slot()


class Home(nustd.ui.Page):
    panel = Panel.slot()


class App(nustd.ui.Index):
    home = Home.slot("/")


LENS = App.home.panel.lens
LENS_PATH = ("home", "panel", "lens")


class _Subscription:
    """A notify the test fires by hand, standing in for the browser."""

    def __init__(self) -> None:
        self.callbacks = []

    def bind(self, cb):
        self.callbacks.append(cb)

    def unbind(self, cb):
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self):
        self.callbacks = []

    def fire(self, payload):
        for cb in tuple(self.callbacks):
            cb(payload)


class _Recorder(nustd.ui.Session):
    """Every frame the program shipped, plus the handles it subscribed with."""

    def __init__(self) -> None:
        self.frames = []
        self.subscriptions = {}

    async def send(self, frame):
        self.frames.append(frame)

    async def aread(self, path):
        return None

    def subscribe(self, path):
        return self.subscriptions.setdefault(path, _Subscription())

    def writes(self, path):
        return [f for f in self.frames if f.op == "write" and f.ref == path]


async def _settle(check, deadline=3.0):
    """Wait for a condition a background arm will satisfy, or give up."""
    waited = 0.0
    while waited < deadline:
        if check():
            return True
        await asyncio.sleep(0.02)
        waited += 0.02
    return False


@pytest.mark.timeout(60)
async def test_the_frame_carries_the_cursor_and_the_columns_and_nothing_else(store):
    """What ships is relative to the Shape. Where it was read from stays here."""
    session = _Recorder()
    await _read(
        store.bind(nustd.ui.Session, session),
        LENS.set_columns(
            nu.List.of(nu.Str("counts")),
            nustd.ui.lens.columns(Zoo, nu.List.of(nu.Str("counts")), prefix=Store.left),
        ),
    )
    (frame,) = session.frames
    assert frame.op == "write"
    assert set(frame.payload) == {"cursor", "columns"}
    assert frame.payload["cursor"] == ["counts"]
    # "left" is where the data lives, and the browser is never told.
    assert "left" not in repr(frame.payload)


@pytest.mark.timeout(60)
async def test_browse_paints_the_root_column_then_repaints_on_a_move(store):
    """The preset, end to end: it brackets its own reads and answers a notify."""
    session = _Recorder()
    ctx = store.bind(nustd.ui.Session, session)
    arm = asyncio.create_task(nu.arun(nustd.ui.lens.browse(LENS, Zoo, prefix=Store.left), ctx))
    try:
        assert await _settle(lambda: session.writes(LENS_PATH))
        # Painted before the browser said anything: the empty cursor is the one
        # cursor known ahead of time.
        boot = session.writes(LENS_PATH)[0].payload
        assert boot["cursor"] == []
        assert [c["kind"] for c in boot["columns"]] == ["shape"]

        session.subscriptions[LENS_PATH].fire(["counts", "red"])
        assert await _settle(lambda: len(session.writes(LENS_PATH)) > 1)
        moved = session.writes(LENS_PATH)[-1].payload
        assert moved["cursor"] == ["counts", "red"]
        assert [c["kind"] for c in moved["columns"]] == ["shape", "mapping", "leaf"]
        assert moved["columns"][-1]["entries"][0]["preview"] == "3"
    finally:
        arm.cancel()


@pytest.mark.timeout(60)
async def test_two_lenses_on_one_page_do_not_share_a_cursor():
    """The arm's attrs key comes off the slot chain, so two lenses are two keys."""

    class Pair(nustd.ui.Page):
        left = Panel.slot()
        right = Panel.slot()

    class Two(nustd.ui.Index):
        pair = Pair.slot("/")

    assert _nav_key(Two.pair.left.lens) != _nav_key(Two.pair.right.lens)
    assert _nav_key(Two.pair.left.lens) == _nav_key(Two.pair.left.lens)
