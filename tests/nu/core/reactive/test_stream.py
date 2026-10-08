"""Tests for the Stream flow: drain-then-follow over ordered collections.

Construction checks run without a substrate. The drain/follow execution loop
requires a real substrate with ordered collection semantics and is deferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import nu
from nu.core.reactive.stream import Stream
from nu.domains.shape.sequence import SequenceRef
from nu.lang import Context, Literal, StreamQuery


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_stream_is_stream_query():
    assert issubclass(Stream, StreamQuery)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_stream_constructs_with_source_and_body():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body)
    # Stream builds advance + change + body + key + log_key = 5 children
    assert len(nu.tree.children(s)) == 5


def test_stream_constructs_with_custom_keys():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body, key="my_key", log_key="my_log_key")
    assert len(nu.tree.children(s)) == 5


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_stream_sync_compile_raises():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body)
    with pytest.raises(NotImplementedError, match="async"):
        s._compile(0, ())


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs real ordered collection backing store")
async def test_stream_drains_existing_items():
    pass


@pytest.mark.skip(reason="substrate impl deferred — needs real ordered collection backing store")
async def test_stream_follows_new_items():
    pass


# ---------------------------------------------------------------------------
# Cursor scope: driven through the compiled thunk with hand-made children
# ---------------------------------------------------------------------------


class _Sub:
    """A change subscription that never fires."""

    def bind(self, receiver: object) -> None:
        pass

    def unbind(self, receiver: object) -> None:
        pass

    def close(self) -> None:
        pass


async def test_stream_cursor_lives_for_the_drain_only() -> None:
    ctx = Context()
    rt = type("Rt", (), {"ctx": ctx})()
    entries = iter([("log-1", "a"), ("log-2", "b")])
    seen: list = []

    async def advance(rt: object) -> object:
        return next(entries, None)

    async def change(rt: object) -> _Sub:
        return _Sub()

    async def body(rt: Runtime) -> object:
        seen.append((rt.ctx.attrs.get("key"), rt.ctx.attrs.get("log")))
        return [rt.ctx.attrs.get("key")]

    async def name(value: str) -> str:
        return value

    children = (advance, change, body, lambda rt: name("key"), lambda rt: name("log"))
    agen = await Stream(Literal(None), Literal(None))._acompile(0, children)(rt)
    assert [await agen.__anext__(), await agen.__anext__()] == ["a", "b"]
    assert seen == [("a", "log-1"), ("b", "log-2")]  # advanced item by item
    assert ctx.attrs.get("log") == "log-2"  # still bound while the stream is open
    await agen.aclose()
    assert ctx.attrs.exists("log") is False  # gone once the stream is closed
    assert ctx.attrs.exists("key") is False
