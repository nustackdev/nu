"""The program flows: ``boot``, ``Ref.showing`` and ``route``.

Wire only, through a fake session that plays the browser's History: a read
answers where the page is, and ``move`` lands a move the way the kit's
HistoryRef reports one, a notify carrying the new uri.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
import nustd.ui as ui
from nu import Context
from nustd.ui import Session
from nustd.ui.refs import trim_slash


class _Sub:
    def __init__(self, session: _History, path: tuple[str, ...]) -> None:
        self.session = session
        self.path = path
        self.callbacks: list = []

    def bind(self, cb) -> None:
        self.callbacks.append(cb)

    def unbind(self, cb) -> None:
        self.callbacks = [c for c in self.callbacks if c is not cb]

    def close(self) -> None:
        self.session.subs.remove(self)


class _History:
    """Fake session: records frames, answers reads with the page's uri."""

    def __init__(self, uri: str = "/") -> None:
        self.uri = uri
        self.frames: list = []
        self.subs: list[_Sub] = []

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    async def aread(self, path: tuple[str, ...]) -> object:
        return self.uri

    def subscribe(self, path: tuple[str, ...]) -> _Sub:
        sub = _Sub(self, path)
        self.subs.append(sub)
        return sub

    def move(self, uri: str) -> None:
        self.uri = uri
        for sub in tuple(self.subs):
            for cb in tuple(sub.callbacks):
                cb(uri)

    def ops(self) -> list[tuple[str, tuple[str, ...]]]:
        """What reached the tab, as (op, path), reads and history writes aside."""
        return [(f.op, f.ref) for f in self.frames]

    def take(self) -> list[tuple[str, tuple[str, ...]]]:
        out = self.ops()
        self.frames = []
        return out


async def _settle() -> None:
    for _ in range(20):
        await asyncio.sleep(0)


class Home(ui.Column):
    heading = ui.HeadingRef.slot(label="Home")


class Detail(ui.Column):
    heading = ui.HeadingRef.slot(label="Detail")


class App(nu.Shape):
    title = ui.TitleRef.slot()
    history = ui.HistoryRef.slot()
    home = Home.slot()
    detail = Detail.slot()
    lost = ui.TextRef.slot()


INIT_HOME = [("init", ("home",)), ("init", ("home", "heading"))]
INIT_DETAIL = [("init", ("detail",)), ("init", ("detail", "heading"))]


def _drive(sess: _History, term, steps):
    """Run ``term`` as a tab would, apply each step between settles, then close the tab."""

    async def main() -> list:
        task = asyncio.ensure_future(nu.arun(term, Context().bind(Session, sess)))
        seen = []
        await _settle()
        seen.append(sess.take())
        for step in steps:
            step()
            await _settle()
            seen.append(sess.take())
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        seen.append(sess.take())
        return seen

    return asyncio.run(main())


# --- boot --------------------------------------------------------------------


def test_boot_clears_the_tab_then_inits_in_order():
    sess = _History()
    asyncio.run(nu.arun(ui.boot(App.title, App.home), Context().bind(Session, sess)))
    assert sess.ops() == [("remove", ()), ("init", ("title",)), *INIT_HOME]


def test_boot_with_nothing_only_clears():
    sess = _History()
    asyncio.run(nu.arun(ui.boot(), Context().bind(Session, sess)))
    assert sess.ops() == [("remove", ())]


# --- showing -----------------------------------------------------------------


def test_showing_inits_parks_and_erases_on_cancel():
    sess = _History()
    [entered, left] = _drive(sess, App.home.showing(App.home.heading.set("Hi")), [])
    assert entered == [*INIT_HOME, ("write", ("home", "heading"))]
    assert left == [("remove", ("home",))]


def test_showing_without_a_body_still_parks():
    sess = _History()
    [entered, left] = _drive(sess, App.home.showing(), [])
    assert entered == INIT_HOME
    assert left == [("remove", ("home",))]


def test_showing_keep_hides_and_displays():
    sess = _History()
    [entered, left] = _drive(sess, App.home.showing(keep=True), [])
    assert entered == [*INIT_HOME, ("display", ("home",))]
    assert left == [("hide", ("home",))]


def test_showing_erases_when_the_body_raises():
    sess = _History()
    term = App.home.showing(nu.Raise("boom", exc_cls=ValueError))
    with pytest.raises(ValueError, match="boom"):
        asyncio.run(nu.arun(term, Context().bind(Session, sess)))
    assert sess.ops() == [*INIT_HOME, ("remove", ("home",))]


def test_a_leave_that_cannot_reach_the_tab_is_quiet():
    class _Gone(_History):
        async def send(self, frame) -> None:
            if frame.op == "remove":
                raise RuntimeError("socket closed")
            await super().send(frame)

    sess = _Gone()
    [entered, left] = _drive(sess, App.home.showing(), [])
    assert entered == INIT_HOME
    assert left == []


# --- route -------------------------------------------------------------------


def _app_route(**kw):
    return ui.route(
        App.history,
        {"/": App.home.showing(), "/detail": App.detail.showing()},
        **kw,
    )


def test_route_runs_the_branch_the_page_is_on():
    sess = _History("/detail?id=3")
    [entered, left] = _drive(sess, _app_route(), [])
    assert entered == INIT_DETAIL
    assert left == [("remove", ("detail",))]


def test_route_switches_on_a_path_move_and_takes_the_old_page_away():
    sess = _History("/")
    seen = _drive(sess, _app_route(), [lambda: sess.move("/detail"), lambda: sess.move("/")])
    assert seen == [
        INIT_HOME,
        [("remove", ("home",)), *INIT_DETAIL],
        [("remove", ("detail",)), *INIT_HOME],
        [("remove", ("home",))],
    ]


def test_a_query_hash_or_same_path_move_reruns_nothing():
    sess = _History("/")
    seen = _drive(
        sess,
        _app_route(),
        [
            lambda: sess.move("/?q=x"),
            lambda: sess.move("/#top"),
            lambda: sess.move("/"),
        ],
    )
    assert seen[1:4] == [[], [], []]


def test_a_trailing_slash_is_the_same_path():
    sess = _History("/detail/")
    seen = _drive(sess, _app_route(), [lambda: sess.move("/detail")])
    assert seen[0] == INIT_DETAIL
    assert seen[1] == []


def test_the_fallback_runs_on_a_path_no_branch_names():
    sess = _History("/nope")
    seen = _drive(
        sess,
        _app_route(fallback=App.lost.showing(App.lost.set("No page here"))),
        [lambda: sess.move("/also-nope"), lambda: sess.move("/")],
    )
    assert seen[0] == [("init", ("lost",)), ("write", ("lost",))]
    # Another unmatched path is another path: the fallback runs again for it.
    assert seen[1] == [("remove", ("lost",)), ("init", ("lost",)), ("write", ("lost",))]
    assert seen[2] == [("remove", ("lost",)), *INIT_HOME]


def test_no_fallback_shows_nothing():
    sess = _History("/nope")
    seen = _drive(sess, _app_route(), [lambda: sess.move("/")])
    assert seen[0] == []
    assert seen[1] == INIT_HOME


def test_a_branch_that_moves_the_page_is_heard():
    # The branch pushes, the kit reports its own move like any other.
    sess = _History("/")

    async def main() -> list:
        term = ui.route(
            App.history,
            {"/": App.home.showing(App.history.push("/detail")), "/detail": App.detail.showing()},
        )
        task = asyncio.ensure_future(nu.arun(term, Context().bind(Session, sess)))
        await _settle()
        push = next(f for f in sess.frames if f.ref == ("history",))
        assert push.payload == {"action": "push", "uri": "/detail"}
        sess.move("/detail")
        await _settle()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return [op for op in sess.ops() if op[1] != ("history",)]

    assert asyncio.run(main()) == [
        *INIT_HOME,
        ("remove", ("home",)),
        *INIT_DETAIL,
        ("remove", ("detail",)),
    ]


def test_route_paths_are_checked():
    with pytest.raises(ValueError, match="starts with"):
        ui.route(App.history, {"detail": nu.Noop()})
    with pytest.raises(ValueError, match="same path"):
        ui.route(App.history, {"/a": nu.Noop(), "/a/": nu.Noop()})


@pytest.mark.parametrize(
    ("raw", "trimmed"),
    [("/", "/"), ("/feed/", "/feed"), ("/feed", "/feed"), ("", ""), ("/a/b/", "/a/b")],
)
def test_trim_slash_is_the_kits(raw, trimmed):
    assert trim_slash(raw) == trimmed
