"""Unit tests for ``nu2.lang.sentinels``.

Covers ``EMPTY`` / ``INVALID`` singletons, the ``Sentinel`` base, and the
``is_empty`` / ``is_invalid`` / ``is_sentinel`` type guards. The atom
dispatch contract reads sentinels by identity, so these tests pin
identity, equality, hashability, falsy boolean, and the guards.
"""

from __future__ import annotations

from nu2.lang.sentinels import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
)


# --- module singletons --------------------------------------------------


def test_empty_is_an_empty_instance() -> None:
    assert isinstance(EMPTY, Empty)
    assert isinstance(EMPTY, Sentinel)


def test_invalid_is_an_invalid_instance() -> None:
    assert isinstance(INVALID, Invalid)
    assert isinstance(INVALID, Sentinel)


def test_empty_and_invalid_are_distinct() -> None:
    assert EMPTY is not INVALID
    assert not isinstance(EMPTY, Invalid)
    assert not isinstance(INVALID, Empty)


# --- value semantics ----------------------------------------------------


def test_sentinels_are_falsy() -> None:
    assert not EMPTY
    assert not INVALID


def test_sentinels_repr_is_stable() -> None:
    assert repr(EMPTY) == "<EMPTY>"
    assert repr(INVALID) == "<INVALID>"


def test_sentinel_equality_is_class_based() -> None:
    assert EMPTY == Empty()
    assert INVALID == Invalid()
    assert EMPTY != INVALID


def test_sentinels_are_hashable() -> None:
    assert hash(EMPTY) == hash(Empty())
    assert hash(INVALID) == hash(Invalid())
    assert {EMPTY, INVALID} == {EMPTY, INVALID}


# --- guards -------------------------------------------------------------


def test_is_empty_matches_empty_only() -> None:
    assert is_empty(EMPTY)
    assert not is_empty(INVALID)
    assert not is_empty(0)
    assert not is_empty(None)
    assert not is_empty("")


def test_is_invalid_matches_invalid_only() -> None:
    assert is_invalid(INVALID)
    assert not is_invalid(EMPTY)
    assert not is_invalid(0)
    assert not is_invalid(None)


def test_is_sentinel_matches_either_sentinel() -> None:
    assert is_sentinel(EMPTY)
    assert is_sentinel(INVALID)
    assert not is_sentinel(0)
    assert not is_sentinel(None)
    assert not is_sentinel(False)
    assert not is_sentinel("")
