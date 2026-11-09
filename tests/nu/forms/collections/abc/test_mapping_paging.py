"""Paged key reads: ``keys(after=, limit=)`` and ``reversed_keys(before=, limit=)``.

The form forwards the args to the runtime mapping's own ``keys`` /
``reversed_keys`` and collects the page into a list. The runtime mapping must be
a ``PagedMapping``: core calls that declared contract, it never probes. No args
reads as before.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu.forms import Dict
from nu.forms.collections.abc import PagedMapping
from nu.forms.collections.abc.mapping_interactions import (
    Keys,
    KeysPage,
    ReversedKeys,
    ReversedKeysPage,
)
from nu.lang.literal import Literal


class _Paged(dict):
    """A dict that pages its keys in insertion order, the contract a store view keeps."""

    def keys(self, *, after=None, limit=None):  # type: ignore[override]
        if after is None and limit is None:
            return super().keys()
        return self._page(list(self), after, limit)

    def reversed_keys(self, *, before=None, limit=None):
        return self._page(list(reversed(self)), before, limit)

    @staticmethod
    def _page(order, cursor, limit):
        start = 0 if cursor is None else order.index(cursor) + 1
        stop = None if limit is None else start + limit
        return iter(order[start:stop])


PagedMapping.register(_Paged)


def _paged() -> Dict:
    return Dict(Literal(_Paged(a=1, b=2, c=3, d=4)))


def test_no_args_builds_the_plain_reads():
    d = Dict({"a": 1})
    assert isinstance(nu.tree.children(d.keys())[0], Keys)
    assert isinstance(nu.tree.children(d.reversed_keys())[0], ReversedKeys)


def test_args_build_the_paged_reads():
    d = Dict({"a": 1})
    assert isinstance(nu.tree.children(d.keys(limit=1))[0], KeysPage)
    assert isinstance(nu.tree.children(d.reversed_keys(before="a"))[0], ReversedKeysPage)


def test_keys_page():
    d = _paged()
    assert nu.run(d.keys(limit=2))[0] == ["a", "b"]
    assert nu.run(d.keys(after="b", limit=2))[0] == ["c", "d"]
    assert nu.run(d.keys(after="c"))[0] == ["d"]


def test_reversed_keys_page():
    d = _paged()
    assert nu.run(d.reversed_keys(limit=2))[0] == ["d", "c"]
    assert nu.run(d.reversed_keys(before="c", limit=5))[0] == ["b", "a"]


def test_pages_read_alike_under_arun():
    d = _paged()
    assert asyncio.run(nu.arun(d.keys(after="a", limit=2)))[0] == ["b", "c"]
    assert asyncio.run(nu.arun(d.reversed_keys(before="d", limit=1)))[0] == ["c"]


def test_no_args_reads_as_before():
    d = _paged()
    assert list(nu.run(d.keys())[0]) == ["a", "b", "c", "d"]
    assert list(nu.run(d.reversed_keys())[0]) == ["d", "c", "b", "a"]


def test_args_are_read_at_run_time():
    class Cursor(nu.Shape):
        after = nu.StrRef.slot()
        limit = nu.IntRef.slot()

    ctx = nu.Context().bind(dict, {"after": "a", "limit": 2}, Cursor)
    term = _paged().keys(after=Cursor.after, limit=Cursor.limit)
    assert nu.run(term, ctx)[0] == ["b", "c"]


def test_a_mapping_that_is_no_paged_mapping_raises():
    with pytest.raises(TypeError, match="PagedMapping"):
        nu.run(Dict({"a": 1}).keys(limit=1))
    with pytest.raises(TypeError, match="PagedMapping"):
        nu.run(Dict({"a": 1}).reversed_keys(limit=1))
    with pytest.raises(TypeError, match="PagedMapping"):
        asyncio.run(nu.arun(Dict({"a": 1}).keys(after="a")))


def test_a_mapping_with_paged_keys_but_not_registered_raises():
    """Core calls the declared contract: a matching method alone is not it."""

    class Unregistered(dict):
        def keys(self, *, after=None, limit=None):  # type: ignore[override]
            return iter(())

        def reversed_keys(self, *, before=None, limit=None):
            return iter(())

    with pytest.raises(TypeError, match="PagedMapping"):
        nu.run(Dict(Literal(Unregistered(a=1))).keys(limit=1))


def test_a_kv_dict_pages_through_its_view():
    pytest.importorskip("nustd.kv")
    from nustd.kv import DictRef, LogDictRef
    from virtuals import Navigator
    from virtuals.codecs import BinaryCodec
    from virtuals.storages.mem import InMemoryStorage
    from virtuals.tkv.storage import TransactionProtocol

    class Board(nu.Shape):
        rows = DictRef.slot(int)
        log = LogDictRef.slot(int)

    with InMemoryStorage(codec=BinaryCodec()) as storage, storage.transaction() as tx:
        ctx = nu.Context().bind(Navigator, Navigator(storage)).bind(TransactionProtocol, tx)
        for i, k in enumerate("dbca"):
            nu.run(Board.rows.set_item(k, i), ctx)
            nu.run(Board.log.set_item(k, i), ctx)
        # a dict pages in key order, a log in insertion order
        assert nu.run(Board.rows.keys(after="a", limit=2), ctx)[0] == ["b", "c"]
        assert nu.run(Board.rows.reversed_keys(before="d", limit=2), ctx)[0] == ["c", "b"]
        assert nu.run(Board.log.keys(after="d", limit=2), ctx)[0] == ["b", "c"]
        assert nu.run(Board.log.reversed_keys(limit=1), ctx)[0] == ["a"]


class _Recording(dict):
    """Records every paging call it gets, to show a NULL arg never reaches it."""

    seen: list

    def keys(self, *, after=None, limit=None):  # type: ignore[override]
        type(self).seen.append((after, limit))
        return iter(())

    def reversed_keys(self, *, before=None, limit=None):
        type(self).seen.append((before, limit))
        return iter(())


PagedMapping.register(_Recording)


class _Cursor(nu.Shape):
    key = nu.StrRef.slot()
    limit = nu.IntRef.slot()


def _null_pages(d):
    return (
        d.keys(after=_Cursor.key),
        d.keys(limit=_Cursor.limit),
        d.reversed_keys(before=_Cursor.key),
        d.reversed_keys(limit=_Cursor.limit),
    )


def test_a_null_cursor_or_limit_raises_before_the_mapping_is_called():
    _Recording.seen = []
    ctx = nu.Context().bind(dict, {}, _Cursor)
    for page in _null_pages(Dict(Literal(_Recording()))):
        with pytest.raises(ValueError, match="read NULL"):
            nu.run(page, ctx)
    assert _Recording.seen == []


def test_a_null_cursor_or_limit_raises_async():
    _Recording.seen = []
    ctx = nu.Context().bind(dict, {}, _Cursor)
    for page in _null_pages(Dict(Literal(_Recording()))):
        with pytest.raises(ValueError, match="read NULL"):
            asyncio.run(nu.arun(page, ctx))
    assert _Recording.seen == []


def test_a_kv_page_raises_on_a_null_cursor_or_limit():
    pytest.importorskip("nustd.kv")
    from nustd.kv import DictRef, LogDictRef
    from virtuals import Navigator
    from virtuals.codecs import BinaryCodec
    from virtuals.storages.mem import InMemoryStorage
    from virtuals.tkv.storage import TransactionProtocol

    class Board(nu.Shape):
        rows = DictRef.slot(int)
        log = LogDictRef.slot(int)

    with InMemoryStorage(codec=BinaryCodec()) as storage, storage.transaction() as tx:
        ctx = (
            nu.Context()
            .bind(Navigator, Navigator(storage))
            .bind(TransactionProtocol, tx)
            .bind(dict, {}, _Cursor)
        )
        for ref in (Board.rows, Board.log):
            nu.run(ref.set_item("a", 1), ctx)
            for page in _null_pages(ref):
                with pytest.raises(ValueError, match="read NULL"):
                    nu.run(page, ctx)
