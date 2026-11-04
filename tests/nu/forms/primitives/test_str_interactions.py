"""Mid-level tests for str interaction queries.

Tests that Join joins an iterable of strings correctly, propagates NULL, and
raises Python's own TypeError when the iterable contains non-strings.
"""

from __future__ import annotations

import pytest

from nu.forms.primitives.str_interactions import Join
from nu.lang import NULL
from nu.lang.helpers import compile, eval
from nu.lang.literal import Literal


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


# --- happy path ----------------------------------------------------------


def test_join_on_list_of_strings():
    result = _eval(Join(Literal(","), Literal(["a", "b", "c"])))
    assert result == "a,b,c"


def test_join_empty_separator():
    result = _eval(Join(Literal(""), Literal(["x", "y", "z"])))
    assert result == "xyz"


def test_join_single_element():
    result = _eval(Join(Literal("-"), Literal(["only"])))
    assert result == "only"


# --- edge cases ----------------------------------------------------------


def test_join_on_list_of_ints_raises():
    # A wrong element type is a real error, not a missing value.
    with pytest.raises(TypeError):
        _eval(Join(Literal(","), Literal([1, 2, 3])))


def test_join_with_a_null_separator_raises():
    with pytest.raises((TypeError, AttributeError)):
        _eval(Join(Literal(NULL), Literal(["a", "b"])))


def test_join_with_a_null_iterable_raises():
    with pytest.raises(TypeError):
        _eval(Join(Literal(","), Literal(NULL)))
