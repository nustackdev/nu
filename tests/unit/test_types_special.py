"""Unit tests for types/special.py module.

Tests for special sentinel values used in ABC modules:
- Empty: sentinel for non-existent values
- NaN: sentinel for invalid operations
- Type guard functions and propagation logic
"""

from everyshape.typing import (
    EMPTY,
    NAN,
    Empty,
    NaN,
    Sentinel,
    is_empty,
    is_nan,
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
    """Test that NAN singleton exists and is a NaN instance."""
    assert NAN is not None
    assert isinstance(NAN, NaN)


def test_singletons_are_special_values() -> None:
    """Test that singletons are instances of Sentinel."""
    assert isinstance(EMPTY, Sentinel)
    assert isinstance(NAN, Sentinel)


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
    assert EMPTY != NAN
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
# NAN CLASS TESTS
# ============================================================================


def test_nan_repr() -> None:
    """Test NaN.__repr__ returns debug representation."""
    assert repr(NAN) == "<NaN>"


def test_nan_str() -> None:
    """Test NaN.__str__ returns display representation."""
    assert str(NAN) == "NaN"


def test_nan_bool() -> None:
    """Test NaN.__bool__ always returns False."""
    assert bool(NAN) is False
    assert not NAN


def test_nan_eq_with_same_instance() -> None:
    """Test NaN.__eq__ returns True for same instance."""
    assert NAN == NAN


def test_nan_eq_with_new_instance() -> None:
    """Test NaN.__eq__ returns True for different NaN instances."""
    nan2 = NaN()
    assert NAN == nan2


def test_nan_eq_with_other_types() -> None:
    """Test NaN.__eq__ returns False for non-NaN values."""
    assert NAN != EMPTY
    assert NAN != None
    assert NAN != ""
    assert NAN != 0
    assert NAN != False


def test_nan_hash() -> None:
    """Test NaN.__hash__ returns consistent hash."""
    nan2 = NaN()
    assert hash(NAN) == hash(nan2)


def test_nan_hashable() -> None:
    """Test NaN can be used in sets and dicts."""
    nan_set = {NAN}
    assert NAN in nan_set

    nan_dict = {NAN: "value"}
    assert nan_dict[NAN] == "value"


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
    assert is_empty(NAN) is False
    assert is_empty(None) is False
    assert is_empty("") is False
    assert is_empty(0) is False
    assert is_empty(False) is False
    assert is_empty([]) is False


def test_is_nan_with_nan_singleton() -> None:
    """Test is_nan() returns True for NAN singleton."""
    assert is_nan(NAN) is True


def test_is_nan_with_nan_instance() -> None:
    """Test is_nan() returns True for NaN instances."""
    nan = NaN()
    assert is_nan(nan) is True


def test_is_nan_with_non_nan() -> None:
    """Test is_nan() returns False for non-NaN values."""
    assert is_nan(EMPTY) is False
    assert is_nan(None) is False
    assert is_nan("") is False
    assert is_nan(0) is False
    assert is_nan(False) is False
    assert is_nan([]) is False


def test_is_sentinel_with_empty() -> None:
    """Test is_sentinel() returns True for Empty instances."""
    assert is_sentinel(EMPTY) is True
    assert is_sentinel(Empty()) is True


def test_is_sentinel_with_nan() -> None:
    """Test is_sentinel() returns True for NaN instances."""
    assert is_sentinel(NAN) is True
    assert is_sentinel(NaN()) is True


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
    """Test propagate_special() with single Empty returns NAN."""
    result = propagate_special(EMPTY)
    assert result is NAN


def test_propagate_special_single_nan() -> None:
    """Test propagate_special() with single NaN returns NAN."""
    result = propagate_special(NAN)
    assert result is NAN


def test_propagate_special_nan_with_normal_values() -> None:
    """Test propagate_special() returns NAN if any value is NaN."""
    result = propagate_special(1, NAN, 3)
    assert result is NAN


def test_propagate_special_nan_priority() -> None:
    """Test propagate_special() checks NaN before Empty."""
    result = propagate_special(EMPTY, NAN)
    assert result is NAN


def test_propagate_special_empty_with_normal_values() -> None:
    """Test propagate_special() returns NAN if any value is Empty (no NaN)."""
    result = propagate_special(1, EMPTY, 3)
    assert result is NAN


def test_propagate_special_multiple_empty() -> None:
    """Test propagate_special() with multiple Empty returns NAN."""
    result = propagate_special(EMPTY, EMPTY)
    assert result is NAN


def test_propagate_special_multiple_nan() -> None:
    """Test propagate_special() with multiple NaN returns NAN."""
    result = propagate_special(NAN, NAN)
    assert result is NAN


def test_propagate_special_mixed_normal() -> None:
    """Test propagate_special() with mixed normal values returns None."""
    result = propagate_special(1, "string", [], {}, None)
    assert result is None


def test_propagate_special_empty_instances() -> None:
    """Test propagate_special() works with Empty instances."""
    empty = Empty()
    result = propagate_special(1, empty, 3)
    assert result is NAN


def test_propagate_special_nan_instances() -> None:
    """Test propagate_special() works with NaN instances."""
    nan = NaN()
    result = propagate_special(1, nan, 3)
    assert result is NAN
