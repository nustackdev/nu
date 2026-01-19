"""Unit tests for types/special.py module.

Tests for special sentinel values used in ABC modules:
- Empty: sentinel for non-existent values
- Invalid: sentinel for invalid operations
- Type guard functions and propagation logic
"""

from pv.typing import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)


# ============================================================================
# SINGLETON TESTS
# ============================================================================


def test_empty_singleton_exists() -> None:
    """Test that EMPTY singleton exists and is an Empty instance."""
    assert EMPTY is not None
    assert isinstance(EMPTY, Empty)


def test_nan_singleton_exists() -> None:
    """Test that INVALID singleton exists and is a Invalid instance."""
    assert INVALID is not None
    assert isinstance(INVALID, Invalid)


def test_singletons_are_special_values() -> None:
    """Test that singletons are instances of Sentinel."""
    assert isinstance(EMPTY, Sentinel)
    assert isinstance(INVALID, Sentinel)


# ============================================================================
# EMPTY CLASS TESTS
# ============================================================================


def test_empty_repr() -> None:
    """Test Empty.__repr__ returns debug representation."""
    assert repr(EMPTY) == "<Empty>"


def test_empty_str() -> None:
    """Test Empty.__str__ returns display representation."""
    assert str(EMPTY) == "Empty"


def test_empty_bool() -> None:
    """Test Empty.__bool__ always returns False."""
    assert bool(EMPTY) is False
    assert not EMPTY


def test_empty_eq_with_same_instance() -> None:
    """Test Empty.__eq__ returns True for same instance."""
    assert EMPTY == EMPTY


def test_empty_eq_with_new_instance() -> None:
    """Test Empty.__eq__ returns True for different Empty instances."""
    empty2 = Empty()
    assert EMPTY == empty2


def test_empty_eq_with_other_types() -> None:
    """Test Empty.__eq__ returns False for non-Empty values."""
    assert EMPTY != INVALID
    assert EMPTY != None
    assert EMPTY != ""
    assert EMPTY != 0
    assert EMPTY != False


def test_empty_hash() -> None:
    """Test Empty.__hash__ returns consistent hash."""
    empty2 = Empty()
    assert hash(EMPTY) == hash(empty2)


def test_empty_hashable() -> None:
    """Test Empty can be used in sets and dicts."""
    empty_set = {EMPTY}
    assert EMPTY in empty_set

    empty_dict = {EMPTY: "value"}
    assert empty_dict[EMPTY] == "value"


# ============================================================================
# INVALID CLASS TESTS
# ============================================================================


def test_nan_repr() -> None:
    """Test Invalid.__repr__ returns debug representation."""
    assert repr(INVALID) == "<Invalid>"


def test_nan_str() -> None:
    """Test Invalid.__str__ returns display representation."""
    assert str(INVALID) == "Invalid"


def test_nan_bool() -> None:
    """Test Invalid.__bool__ always returns False."""
    assert bool(INVALID) is False
    assert not INVALID


def test_nan_eq_with_same_instance() -> None:
    """Test Invalid.__eq__ returns True for same instance."""
    assert INVALID == INVALID


def test_nan_eq_with_new_instance() -> None:
    """Test Invalid.__eq__ returns True for different Invalid instances."""
    nan2 = Invalid()
    assert INVALID == nan2


def test_nan_eq_with_other_types() -> None:
    """Test Invalid.__eq__ returns False for non-Invalid values."""
    assert INVALID != EMPTY
    assert INVALID != None
    assert INVALID != ""
    assert INVALID != 0
    assert INVALID != False


def test_nan_hash() -> None:
    """Test Invalid.__hash__ returns consistent hash."""
    nan2 = Invalid()
    assert hash(INVALID) == hash(nan2)


def test_nan_hashable() -> None:
    """Test Invalid can be used in sets and dicts."""
    nan_set = {INVALID}
    assert INVALID in nan_set

    nan_dict = {INVALID: "value"}
    assert nan_dict[INVALID] == "value"


# ============================================================================
# TYPE GUARD FUNCTION TESTS
# ============================================================================


def test_is_empty_with_empty_singleton() -> None:
    """Test is_empty() returns True for EMPTY singleton."""
    assert is_empty(EMPTY) is True


def test_is_empty_with_empty_instance() -> None:
    """Test is_empty() returns True for Empty instances."""
    empty = Empty()
    assert is_empty(empty) is True


def test_is_empty_with_non_empty() -> None:
    """Test is_empty() returns False for non-Empty values."""
    assert is_empty(INVALID) is False
    assert is_empty(None) is False
    assert is_empty("") is False
    assert is_empty(0) is False
    assert is_empty(False) is False
    assert is_empty([]) is False


def test_is_invalid_with_nan_singleton() -> None:
    """Test is_invalid() returns True for INVALID singleton."""
    assert is_invalid(INVALID) is True


def test_is_invalid_with_nan_instance() -> None:
    """Test is_invalid() returns True for Invalid instances."""
    invalid = Invalid()
    assert is_invalid(invalid) is True


def test_is_invalid_with_non_nan() -> None:
    """Test is_invalid() returns False for non-Invalid values."""
    assert is_invalid(EMPTY) is False
    assert is_invalid(None) is False
    assert is_invalid("") is False
    assert is_invalid(0) is False
    assert is_invalid(False) is False
    assert is_invalid([]) is False


def test_is_sentinel_with_empty() -> None:
    """Test is_sentinel() returns True for Empty instances."""
    assert is_sentinel(EMPTY) is True
    assert is_sentinel(Empty()) is True


def test_is_sentinel_with_nan() -> None:
    """Test is_sentinel() returns True for Invalid instances."""
    assert is_sentinel(INVALID) is True
    assert is_sentinel(Invalid()) is True


def test_is_sentinel_with_non_special() -> None:
    """Test is_sentinel() returns False for non-special values."""
    assert is_sentinel(None) is False
    assert is_sentinel("") is False
    assert is_sentinel(0) is False
    assert is_sentinel(False) is False
    assert is_sentinel([]) is False
    assert is_sentinel({}) is False


# ============================================================================
# PROPAGATE_SPECIAL FUNCTION TESTS
# ============================================================================


def test_propagate_special_no_args() -> None:
    """Test propagate_special() with no arguments returns None."""
    assert propagate_special() is None


def test_propagate_special_normal_values() -> None:
    """Test propagate_special() with only normal values returns None."""
    assert propagate_special(1, 2, 3) is None
    assert propagate_special("a", "b") is None
    assert propagate_special([], {}) is None


def test_propagate_special_single_empty() -> None:
    """Test propagate_special() with single Empty returns INVALID."""
    result = propagate_special(EMPTY)
    assert result is INVALID


def test_propagate_special_single_nan() -> None:
    """Test propagate_special() with single Invalid returns INVALID."""
    result = propagate_special(INVALID)
    assert result is INVALID


def test_propagate_special_nan_with_normal_values() -> None:
    """Test propagate_special() returns INVALID if any value is Invalid."""
    result = propagate_special(1, INVALID, 3)
    assert result is INVALID


def test_propagate_special_nan_priority() -> None:
    """Test propagate_special() checks Invalid before Empty."""
    result = propagate_special(EMPTY, INVALID)
    assert result is INVALID


def test_propagate_special_empty_with_normal_values() -> None:
    """Test propagate_special() returns INVALID if any value is Empty (no Invalid)."""
    result = propagate_special(1, EMPTY, 3)
    assert result is INVALID


def test_propagate_special_multiple_empty() -> None:
    """Test propagate_special() with multiple Empty returns INVALID."""
    result = propagate_special(EMPTY, EMPTY)
    assert result is INVALID


def test_propagate_special_multiple_nan() -> None:
    """Test propagate_special() with multiple Invalid returns INVALID."""
    result = propagate_special(INVALID, INVALID)
    assert result is INVALID


def test_propagate_special_mixed_normal() -> None:
    """Test propagate_special() with mixed normal values returns None."""
    result = propagate_special(1, "string", [], {}, None)
    assert result is None


def test_propagate_special_empty_instances() -> None:
    """Test propagate_special() works with Empty instances."""
    empty = Empty()
    result = propagate_special(1, empty, 3)
    assert result is INVALID


def test_propagate_special_nan_instances() -> None:
    """Test propagate_special() works with Invalid instances."""
    invalid = Invalid()
    result = propagate_special(1, invalid, 3)
    assert result is INVALID
