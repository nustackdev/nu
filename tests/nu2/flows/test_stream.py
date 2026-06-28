"""Tests for the Stream flow: drain-then-follow over ordered collections.

Construction checks run without a substrate. The drain/follow execution loop
requires a real substrate with ordered collection semantics and is deferred.
"""

from __future__ import annotations

import pytest

from nu2.domains.shape.refs.sequence import SequenceRef
from nu2.flows.stream import Stream
from nu2.lang import StreamQuery


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
    assert len(s.children) == 5


def test_stream_constructs_with_custom_keys():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body, key="my_key", log_key="my_log_key")
    assert len(s.children) == 5


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_stream_sync_compile_raises():
    source = SequenceRef("items")
    body = SequenceRef("body")
    s = Stream(source, body)
    with pytest.raises(NotImplementedError, match="async"):
        s.compile(0, ())


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs real ordered collection backing store")
async def test_stream_drains_existing_items():
    pass


@pytest.mark.skip(reason="substrate impl deferred — needs real ordered collection backing store")
async def test_stream_follows_new_items():
    pass
