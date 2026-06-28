"""Mid-level tests for set interaction queries.

Tests that UnionQuery, IntersectionQuery, DifferenceQuery, and
SymmetricDifferenceQuery accept a list as the right operand (Python's set
methods accept any iterable, not just sets).
"""

from __future__ import annotations

from nu2.core.literal import LiteralQuery
from nu2.forms.collections.abc.set_interactions import (
    DifferenceQuery,
    IntersectionQuery,
    SymmetricDifferenceQuery,
    UnionQuery,
)
from nu2.lang import INVALID, compile
from nu2.lang.helpers import eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


# --- UnionQuery ----------------------------------------------------------


def test_union_accepts_a_list_as_right_operand():
    result = _eval(UnionQuery(LiteralQuery({1, 2}), LiteralQuery([3, 4])))
    assert result == {1, 2, 3, 4}


def test_union_with_duplicate_elements():
    result = _eval(UnionQuery(LiteralQuery({1, 2}), LiteralQuery([2, 3])))
    assert result == {1, 2, 3}


# --- IntersectionQuery ---------------------------------------------------


def test_intersection_accepts_a_list_as_right_operand():
    result = _eval(IntersectionQuery(LiteralQuery({1, 2, 3}), LiteralQuery([2, 3, 4])))
    assert result == {2, 3}


def test_intersection_empty_result():
    result = _eval(IntersectionQuery(LiteralQuery({1, 2}), LiteralQuery([3, 4])))
    assert result == set()


# --- DifferenceQuery -----------------------------------------------------


def test_difference_accepts_a_list_as_right_operand():
    result = _eval(DifferenceQuery(LiteralQuery({1, 2, 3}), LiteralQuery([2, 3])))
    assert result == {1}


def test_difference_with_no_overlap():
    result = _eval(DifferenceQuery(LiteralQuery({1, 2}), LiteralQuery([3, 4])))
    assert result == {1, 2}


# --- SymmetricDifferenceQuery --------------------------------------------


def test_symmetric_difference_accepts_a_list_as_right_operand():
    result = _eval(SymmetricDifferenceQuery(LiteralQuery({1, 2, 3}), LiteralQuery([2, 3, 4])))
    assert result == {1, 4}


def test_symmetric_difference_disjoint_sets():
    result = _eval(SymmetricDifferenceQuery(LiteralQuery({1, 2}), LiteralQuery([3, 4])))
    assert result == {1, 2, 3, 4}


# --- sentinel propagation ------------------------------------------------


def test_union_propagates_invalid_left():
    assert _eval(UnionQuery(LiteralQuery(INVALID), LiteralQuery([1, 2]))) is INVALID


def test_union_propagates_invalid_right():
    assert _eval(UnionQuery(LiteralQuery({1, 2}), LiteralQuery(INVALID))) is INVALID
