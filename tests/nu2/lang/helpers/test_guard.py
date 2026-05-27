"""Unit tests for ``nu2.lang.helpers._guard``.

Covers ``refuse_async_only`` -- it reads the root's
``HAS_ASYNC_ONLY_ATOM`` column and raises a clear RuntimeError pointing
the caller at the async sibling.
"""

from __future__ import annotations

import pytest
from tests.nu2._support.law_terms import Q

from nu2.engine.structure import Declared
from nu2.lang import ScalarQuery, compile
from nu2.lang.helpers._guard import refuse_async_only


class AsyncOnly(ScalarQuery):
    """An inline ScalarQuery declaring requires_async."""

    requires_async = Declared(value=True)


def test_refuse_async_only_passes_for_sync_program():
    prog = compile(Q())
    refuse_async_only(prog, "run", "arun")


def test_refuse_async_only_raises_for_async_only_root():
    prog = compile(AsyncOnly())
    with pytest.raises(RuntimeError):
        refuse_async_only(prog, "run", "arun")


def test_refuse_async_only_message_mentions_entry_and_swap():
    prog = compile(AsyncOnly())
    with pytest.raises(RuntimeError) as excinfo:
        refuse_async_only(prog, "myentry", "myswap")
    msg = str(excinfo.value)
    assert "myentry" in msg
    assert "myswap" in msg


def test_refuse_async_only_message_mentions_async_only():
    prog = compile(AsyncOnly())
    with pytest.raises(RuntimeError, match=r"async-only"):
        refuse_async_only(prog, "run", "arun")


def test_refuse_async_only_passes_for_compiled_q_with_other_entries():
    prog = compile(Q())
    refuse_async_only(prog, "first", "afirst")
    refuse_async_only(prog, "collect", "acollect")
