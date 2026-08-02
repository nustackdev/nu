"""Mid-level tests for set interaction queries.

Tests that Union, Intersection, Difference, and
SymmetricDifference accept a list as the right operand (Python's set
methods accept any iterable, not just sets).
"""

from __future__ import annotations

from nu.core.literal import Literal
from nu.forms.collections.abc.set_interactions import (
    Difference,
    Intersection,
    SymmetricDifference,
    Union,
)
from nu.lang import INVALID, compile
from nu.lang.helpers import eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


# --- Union ----------------------------------------------------------


def test_union_accepts_a_list_as_right_operand():
    result = _eval(Union(Literal({1, 2}), Literal([3, 4])))
    assert result == {1, 2, 3, 4}


def test_union_with_duplicate_elements():
    result = _eval(Union(Literal({1, 2}), Literal([2, 3])))
    assert result == {1, 2, 3}


# --- Intersection ---------------------------------------------------


def test_intersection_accepts_a_list_as_right_operand():
    result = _eval(Intersection(Literal({1, 2, 3}), Literal([2, 3, 4])))
    assert result == {2, 3}


def test_intersection_empty_result():
    result = _eval(Intersection(Literal({1, 2}), Literal([3, 4])))
    assert result == set()


# --- Difference -----------------------------------------------------


def test_difference_accepts_a_list_as_right_operand():
    result = _eval(Difference(Literal({1, 2, 3}), Literal([2, 3])))
    assert result == {1}


def test_difference_with_no_overlap():
    result = _eval(Difference(Literal({1, 2}), Literal([3, 4])))
    assert result == {1, 2}


# --- SymmetricDifference --------------------------------------------


def test_symmetric_difference_accepts_a_list_as_right_operand():
    result = _eval(SymmetricDifference(Literal({1, 2, 3}), Literal([2, 3, 4])))
    assert result == {1, 4}


def test_symmetric_difference_disjoint_sets():
    result = _eval(SymmetricDifference(Literal({1, 2}), Literal([3, 4])))
    assert result == {1, 2, 3, 4}


# --- sentinel propagation ------------------------------------------------


def test_union_propagates_invalid_left():
    assert _eval(Union(Literal(INVALID), Literal([1, 2]))) is INVALID


def test_union_propagates_invalid_right():
    assert _eval(Union(Literal({1, 2}), Literal(INVALID))) is INVALID
