"""Mid-level tests for str interaction queries.

Tests that JoinQuery joins an iterable of strings correctly, and returns INVALID
when the iterable contains non-strings (TypeError is surfaced as INVALID).
"""

from __future__ import annotations

from nu.core.literal import LiteralQuery
from nu.forms.primitives.str_interactions import JoinQuery
from nu.lang import INVALID, compile
from nu.lang.helpers import eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


# --- happy path ----------------------------------------------------------


def test_join_on_list_of_strings():
    result = _eval(JoinQuery(LiteralQuery(","), LiteralQuery(["a", "b", "c"])))
    assert result == "a,b,c"


def test_join_empty_separator():
    result = _eval(JoinQuery(LiteralQuery(""), LiteralQuery(["x", "y", "z"])))
    assert result == "xyz"


def test_join_single_element():
    result = _eval(JoinQuery(LiteralQuery("-"), LiteralQuery(["only"])))
    assert result == "only"


# --- edge cases ----------------------------------------------------------


def test_join_on_list_of_ints_returns_invalid():
    # TypeError from str.join is surfaced as INVALID.
    result = _eval(JoinQuery(LiteralQuery(","), LiteralQuery([1, 2, 3])))
    assert result is INVALID


def test_join_with_invalid_separator_returns_invalid():
    result = _eval(JoinQuery(LiteralQuery(INVALID), LiteralQuery(["a", "b"])))
    assert result is INVALID


def test_join_with_invalid_iterable_returns_invalid():
    result = _eval(JoinQuery(LiteralQuery(","), LiteralQuery(INVALID)))
    assert result is INVALID
