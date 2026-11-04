"""Unit tests for ``nu.lang.sentinels``: UNSET, the internal argument marker."""

from __future__ import annotations

from nu.lang.null import NULL, is_null
from nu.lang.sentinels import EMPTY, UNSET, Sentinel, Unset, is_sentinel


def test_unset_is_a_sentinel() -> None:
    assert isinstance(UNSET, Unset)
    assert isinstance(UNSET, Sentinel)
    assert repr(UNSET) == "<UNSET>"


def test_unset_is_not_null() -> None:
    assert not is_null(UNSET)
    assert UNSET != NULL


def test_is_sentinel_matches_unset_only() -> None:
    assert is_sentinel(UNSET)
    for v in (NULL, 0, None, False, ""):
        assert not is_sentinel(v)


def test_empty_is_a_temporary_alias_of_null() -> None:
    assert EMPTY is NULL
