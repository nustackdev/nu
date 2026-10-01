"""Unit tests for ``nu.lang.sentinels``.

Covers the ``EMPTY`` / ``UNSET`` singletons, the ``Sentinel`` base, and the
``is_empty`` / ``is_sentinel`` type guards. The atom dispatch contract reads
EMPTY by identity, so these tests pin identity, equality, hashability, falsy
boolean, and the guards.
"""

from __future__ import annotations

import nu.lang.sentinels as sentinels
from nu.lang.sentinels import (
    EMPTY,
    UNSET,
    Empty,
    Sentinel,
    is_empty,
    is_sentinel,
)


# --- module singletons --------------------------------------------------


def test_empty_is_an_empty_instance() -> None:
    assert isinstance(EMPTY, Empty)
    assert isinstance(EMPTY, Sentinel)


def test_empty_is_the_only_no_value_sentinel() -> None:
    assert not hasattr(sentinels, "INVALID")
    assert not hasattr(sentinels, "Invalid")
    assert not hasattr(sentinels, "is_invalid")


# --- value semantics ----------------------------------------------------


def test_empty_is_falsy() -> None:
    assert not EMPTY


def test_empty_repr_is_stable() -> None:
    assert repr(EMPTY) == "<EMPTY>"


def test_empty_equality_is_class_based() -> None:
    assert EMPTY == Empty()
    assert EMPTY != None


def test_empty_is_hashable() -> None:
    assert hash(EMPTY) == hash(Empty())
    assert len({EMPTY, Empty()}) == 1


# --- guards -------------------------------------------------------------


def test_is_empty_matches_empty_only() -> None:
    assert is_empty(EMPTY)
    assert not is_empty(UNSET)
    assert not is_empty(0)
    assert not is_empty(None)
    assert not is_empty("")


def test_is_sentinel_matches_any_sentinel() -> None:
    assert is_sentinel(EMPTY)
    assert is_sentinel(UNSET)
    assert not is_sentinel(0)
    assert not is_sentinel(None)
    assert not is_sentinel(False)
    assert not is_sentinel("")
