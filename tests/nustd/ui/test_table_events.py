"""TableRef's two notifies: ``on_sort`` and ``on_row_click`` each take only their own.

A fake subscription fires every payload the moment a reaction binds, so
``React`` runs its body on the first one its filter lets through.
"""

from __future__ import annotations

import asyncio

import nu
from nu import Context
from nustd.ui import Session, TableRef
from nustd.ui.nudle import Index, Page
from nustd.ui.refs import TextRef


class ShelfPage(Page):
    table = TableRef.slot(columns=["title"], clickable_rows=True)
    out = TextRef.slot()


class ShelfApp(Index):
    shelf = ShelfPage.slot("/")


class _Sub:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = payloads

    def bind(self, cb) -> None:
        for p in self.payloads:
            cb(p)

    def unbind(self, cb) -> None:
        pass

    def close(self) -> None:
        pass


class _Session:
    def __init__(self, *payloads: object) -> None:
        self.frames: list = []
        self.payloads = list(payloads)

    async def send(self, frame: object) -> None:
        self.frames.append(frame)

    def subscribe(self, path: tuple[str, ...]) -> _Sub:
        return _Sub(self.payloads)


_SORT = {"event": "sort", "sort_column": "title", "sort_direction": "desc"}
_ROW = {"event": "row", "row_index": 3}


def _run(term: nu.Nu, sess: _Session) -> None:
    asyncio.run(nu.arun(term, Context().bind(Session, sess)))


def test_row_click_skips_a_sort():
    sess = _Session(_SORT, _ROW)
    out = ShelfApp.shelf.out
    _run(
        nu.React(ShelfApp.shelf.table.on_row_click(), lambda c: out.set(nu.str(c["row_index"]))),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["3"]


def test_sort_skips_a_row_click():
    sess = _Session(_ROW, _SORT)
    out = ShelfApp.shelf.out
    _run(
        nu.React(
            ShelfApp.shelf.table.on_sort(),
            lambda s: out.set(nu.Str(s["sort_column"]) + " " + nu.Str(s["sort_direction"])),
        ),
        sess,
    )
    assert [f.payload for f in sess.frames] == ["title desc"]
