from __future__ import annotations

from everyabc.term import (
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


class TestSingletons:
    def test_empty_is_singleton_identity(self):
        from everyabc.term.sentinel import EMPTY as EMPTY_2

        assert EMPTY is EMPTY_2

    def test_invalid_is_singleton_identity(self):
        from everyabc.term.sentinel import INVALID as INVALID_2

        assert INVALID is INVALID_2


class TestEmptyEquality:
    def test_empty_equals_empty(self):
        assert Empty() == Empty()

    def test_empty_equals_singleton(self):
        assert EMPTY == Empty()

    def test_empty_not_equal_to_invalid(self):
        assert EMPTY != INVALID

    def test_empty_not_equal_to_none(self):
        assert EMPTY != None

    def test_empty_not_equal_to_string(self):
        assert EMPTY != "empty"


class TestInvalidEquality:
    def test_invalid_equals_invalid(self):
        assert Invalid() == Invalid()

    def test_invalid_equals_singleton(self):
        assert INVALID == Invalid()

    def test_invalid_not_equal_to_empty(self):
        assert INVALID != EMPTY

    def test_invalid_not_equal_to_none(self):
        assert INVALID != None


class TestBool:
    def test_empty_is_falsy(self):
        assert bool(EMPTY) is False

    def test_invalid_is_falsy(self):
        assert bool(INVALID) is False


class TestRepr:
    def test_empty_repr(self):
        assert repr(EMPTY) == "<Empty>"

    def test_invalid_repr(self):
        assert repr(INVALID) == "<Invalid>"

    def test_empty_str(self):
        assert str(EMPTY) == "<Empty>"

    def test_invalid_str(self):
        assert str(INVALID) == "<Invalid>"


class TestTypeGuards:
    def test_is_empty_true(self):
        assert is_empty(EMPTY) is True

    def test_is_empty_false(self):
        assert is_empty(42) is False

    def test_is_empty_for_invalid(self):
        assert is_empty(INVALID) is False

    def test_is_invalid_true(self):
        assert is_invalid(INVALID) is True

    def test_is_invalid_false(self):
        assert is_invalid(42) is False

    def test_is_invalid_for_empty(self):
        assert is_invalid(EMPTY) is False

    def test_is_sentinel_empty(self):
        assert is_sentinel(EMPTY) is True

    def test_is_sentinel_invalid(self):
        assert is_sentinel(INVALID) is True

    def test_is_sentinel_false(self):
        assert is_sentinel(42) is False

    def test_is_sentinel_none(self):
        assert is_sentinel(None) is False


class TestPropagateSpecial:
    def test_all_normal(self):
        assert propagate_special(1, 2, 3) is None

    def test_empty_propagates(self):
        result = propagate_special(1, EMPTY, 3)
        assert result is INVALID

    def test_invalid_propagates(self):
        result = propagate_special(1, INVALID, 3)
        assert result is INVALID

    def test_both_special(self):
        result = propagate_special(EMPTY, INVALID)
        assert result is INVALID

    def test_no_values(self):
        assert propagate_special() is None

    def test_single_normal(self):
        assert propagate_special(42) is None

    def test_single_empty(self):
        assert propagate_special(EMPTY) is INVALID

    def test_single_invalid(self):
        assert propagate_special(INVALID) is INVALID


class TestSentinelBase:
    def test_empty_is_sentinel(self):
        assert isinstance(EMPTY, Sentinel)

    def test_invalid_is_sentinel(self):
        assert isinstance(INVALID, Sentinel)

    def test_sentinel_base(self):
        s = Sentinel()
        assert isinstance(s, Sentinel)


class TestHashConsistency:
    def test_empty_hash_stable(self):
        assert hash(EMPTY) == hash(Empty())

    def test_invalid_hash_stable(self):
        assert hash(INVALID) == hash(Invalid())

    def test_empty_hash_differs_from_invalid(self):
        assert hash(EMPTY) != hash(INVALID)

    def test_empty_usable_in_set(self):
        s = {EMPTY, Empty()}
        assert len(s) == 1

    def test_invalid_usable_in_set(self):
        s = {INVALID, Invalid()}
        assert len(s) == 1

    def test_empty_usable_as_dict_key(self):
        d = {EMPTY: "empty"}
        assert d[Empty()] == "empty"
