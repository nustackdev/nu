"""Unit tests for the _types module."""

from pv.typing import NOT_SET, NotSet, is_notset


class TestNotSet:
    """Tests for the NotSet sentinel class."""

    def test_not_set_singleton_exists(self) -> None:
        """Test that NOT_SET singleton is created and is an instance of NotSet."""
        assert NOT_SET is not None
        assert isinstance(NOT_SET, NotSet)

    def test_not_set_repr(self) -> None:
        """Test __repr__ returns correct string."""
        assert repr(NOT_SET) == "<NotSet>"

    def test_not_set_str(self) -> None:
        """Test __str__ returns correct string."""
        assert str(NOT_SET) == "NotSet"

    def test_not_set_bool_is_false(self) -> None:
        """Test __bool__ returns False."""
        assert not NOT_SET
        assert NOT_SET.__bool__() is False

    def test_not_set_equals_itself(self) -> None:
        """Test NotSet instance equals itself."""
        assert NOT_SET == NOT_SET

    def test_not_set_equals_other_notset_instance(self) -> None:
        """Test multiple NotSet instances are equal to each other."""
        other_notset = NotSet()
        assert NOT_SET == other_notset
        assert other_notset == NOT_SET

    def test_not_set_not_equals_other_types(self) -> None:
        """Test NotSet does not equal other types."""
        assert NOT_SET != None
        assert NOT_SET != ""
        assert NOT_SET != 0
        assert NOT_SET != False
        assert NOT_SET != []
        assert NOT_SET != {}
        assert NOT_SET != object()

    def test_not_set_hash_is_consistent(self) -> None:
        """Test __hash__ works and is consistent."""
        hash1 = hash(NOT_SET)
        hash2 = hash(NOT_SET)
        assert hash1 == hash2

    def test_not_set_hash_same_for_different_instances(self) -> None:
        """Test different NotSet instances have the same hash."""
        other_notset = NotSet()
        assert hash(NOT_SET) == hash(other_notset)

    def test_not_set_can_be_used_in_set(self) -> None:
        """Test NotSet instances can be added to a set."""
        notset_set = {NOT_SET}
        assert NOT_SET in notset_set

    def test_not_set_can_be_used_as_dict_key(self) -> None:
        """Test NotSet instances can be used as dictionary keys."""
        notset_dict = {NOT_SET: "value"}
        assert notset_dict[NOT_SET] == "value"


class TestIsNotSet:
    """Tests for the is_notset() type guard function."""

    def test_is_notset_with_singleton(self) -> None:
        """Test is_notset() correctly identifies NOT_SET singleton."""
        assert is_notset(NOT_SET) is True

    def test_is_notset_with_new_instance(self) -> None:
        """Test is_notset() correctly identifies a new NotSet instance."""
        other_notset = NotSet()
        assert is_notset(other_notset) is True

    def test_is_notset_with_none(self) -> None:
        """Test is_notset() returns False for None."""
        assert is_notset(None) is False

    def test_is_notset_with_other_types(self) -> None:
        """Test is_notset() returns False for other types."""
        assert is_notset("") is False
        assert is_notset(0) is False
        assert is_notset(False) is False
        assert is_notset([]) is False
        assert is_notset({}) is False
        assert is_notset(object()) is False

    def test_is_notset_type_guard(self) -> None:
        """Test is_notset() works as a type guard."""
        value: object = NOT_SET
        if is_notset(value):
            # Type checker should narrow to NotSet here
            assert isinstance(value, NotSet)
