"""Tests for Ref - typed pointer to a location.

Ref is abstract. Tests verify the protocol contract:
resolve, fetch, execute delegation, and purity.
"""

from __future__ import annotations

import nu
from nu import Context, Nu
from nu.terms.ref import Ref


# ---------------------------------------------------------------------------
# Minimal concrete Ref for testing the abstract protocol
# ---------------------------------------------------------------------------


class StubRef(Ref[int]):
    """Minimal Ref that resolves to a fixed key and fetches a fixed value."""

    def __init__(self, key: str, value: int) -> None:
        super().__init__()
        self._key = key
        self._value = value

    async def resolve(self, ctx: Context) -> str:
        return self._key

    async def fetch(self, ctx: Context) -> int:
        return self._value


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


async def test_resolve(ctx):
    ref = StubRef("loc", 42)
    assert await ref.resolve(ctx) == "loc"


async def test_fetch(ctx):
    ref = StubRef("loc", 42)
    assert await ref.fetch(ctx) == 42


async def test_open_yields_fetched_value(ctx):
    ref = StubRef("loc", 42)
    assert await nu.first(ref, ctx) == 42


async def test_fetch_via_helper(ctx):
    ref = StubRef("loc", 42)
    assert await nu.fetch(ref, ctx) == 42


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_ref_is_leaf():
    ref = StubRef("loc", 42)
    assert ref._is_leaf is True
    assert ref._child_count == 0


def test_ref_is_nu():
    assert isinstance(StubRef("loc", 42), Nu)


def test_ref_is_ref():
    assert isinstance(StubRef("loc", 42), Ref)
