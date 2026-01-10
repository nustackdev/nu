"""Unit tests for everyshape.types.primitive module.

Tests the cast_value() function and verifies it works correctly with all
supported primitive and composite value types.
"""

from everyshape.types.primitive import cast_value


class TestCastValueWithPrimitives:
    """Test cast_value() with primitive types."""

    def test_cast_none(self) -> None:
        """Test casting None value."""
        result = cast_value(None)
        assert result is None

    def test_cast_bytes(self) -> None:
        """Test casting bytes value."""
        value = b"hello"
        result = cast_value(value)
        assert result == value
        assert isinstance(result, bytes)

    def test_cast_bool_true(self) -> None:
        """Test casting bool True value."""
        value = True
        result = cast_value(value)
        assert result is True
        assert isinstance(result, bool)

    def test_cast_bool_false(self) -> None:
        """Test casting bool False value."""
        value = False
        result = cast_value(value)
        assert result is False
        assert isinstance(result, bool)

    def test_cast_int(self) -> None:
        """Test casting int value."""
        value = 42
        result = cast_value(value)
        assert result == value
        assert isinstance(result, int)

    def test_cast_int_negative(self) -> None:
        """Test casting negative int value."""
        value = -100
        result = cast_value(value)
        assert result == value

    def test_cast_int_zero(self) -> None:
        """Test casting zero int value."""
        value = 0
        result = cast_value(value)
        assert result == value

    def test_cast_float(self) -> None:
        """Test casting float value."""
        value = 3.14
        result = cast_value(value)
        assert result == value
        assert isinstance(result, float)

    def test_cast_float_negative(self) -> None:
        """Test casting negative float value."""
        value = -2.71
        result = cast_value(value)
        assert result == value

    def test_cast_float_zero(self) -> None:
        """Test casting zero float value."""
        value = 0.0
        result = cast_value(value)
        assert result == value

    def test_cast_str(self) -> None:
        """Test casting str value."""
        value = "hello world"
        result = cast_value(value)
        assert result == value
        assert isinstance(result, str)

    def test_cast_str_empty(self) -> None:
        """Test casting empty string value."""
        value = ""
        result = cast_value(value)
        assert result == value

    def test_cast_complex(self) -> None:
        """Test casting complex number value."""
        value = 3 + 4j
        result = cast_value(value)
        assert result == value
        assert isinstance(result, complex)


class TestCastValueWithComposites:
    """Test cast_value() with composite types."""

    def test_cast_list_empty(self) -> None:
        """Test casting empty list."""
        value = []
        result = cast_value(value)
        assert result == value
        assert isinstance(result, list)

    def test_cast_list_with_primitives(self) -> None:
        """Test casting list with primitive values."""
        value = [1, "hello", 3.14, True]
        result = cast_value(value)
        assert result == value
        assert isinstance(result, list)

    def test_cast_list_with_mixed_types(self) -> None:
        """Test casting list with mixed primitive types."""
        value = [None, b"bytes", 42, "string"]
        result = cast_value(value)
        assert result == value

    def test_cast_set_empty(self) -> None:
        """Test casting empty set."""
        value = set()
        result = cast_value(value)
        assert result == value
        assert isinstance(result, set)

    def test_cast_set_with_primitives(self) -> None:
        """Test casting set with primitive values."""
        value = {1, 2, 3, "hello"}
        result = cast_value(value)
        assert result == value
        assert isinstance(result, set)

    def test_cast_dict_empty(self) -> None:
        """Test casting empty dict."""
        value = {}
        result = cast_value(value)
        assert result == value
        assert isinstance(result, dict)

    def test_cast_dict_with_primitives(self) -> None:
        """Test casting dict with primitive values."""
        value = {"name": "Alice", "age": 30, "active": True}
        result = cast_value(value)
        assert result == value
        assert isinstance(result, dict)

    def test_cast_dict_with_mixed_values(self) -> None:
        """Test casting dict with mixed type values."""
        value = {"none": None, "int": 42, "float": 3.14, "str": "test"}
        result = cast_value(value)
        assert result == value

    def test_cast_tuple_empty(self) -> None:
        """Test casting empty tuple."""
        value = ()
        result = cast_value(value)
        assert result == value
        assert isinstance(result, tuple)

    def test_cast_tuple_with_primitives(self) -> None:
        """Test casting tuple with primitive values."""
        value = (1, "hello", 3.14, True, None)
        result = cast_value(value)
        assert result == value
        assert isinstance(result, tuple)

    def test_cast_tuple_with_mixed_types(self) -> None:
        """Test casting tuple with mixed types."""
        value = (42, "string", b"bytes", True)
        result = cast_value(value)
        assert result == value

    def test_cast_frozenset_empty(self) -> None:
        """Test casting empty frozenset."""
        value = frozenset()
        result = cast_value(value)
        assert result == value
        assert isinstance(result, frozenset)

    def test_cast_frozenset_with_primitives(self) -> None:
        """Test casting frozenset with primitive values."""
        value = frozenset({1, 2, 3, "hello"})
        result = cast_value(value)
        assert result == value
        assert isinstance(result, frozenset)


class TestCastValueWithNestedComposites:
    """Test cast_value() with nested composite structures."""

    def test_cast_list_with_nested_list(self) -> None:
        """Test casting list containing nested lists."""
        value = [1, [2, 3], "hello"]
        result = cast_value(value)
        assert result == value

    def test_cast_list_with_nested_dict(self) -> None:
        """Test casting list containing nested dict."""
        value = [1, {"key": "value"}, 3]
        result = cast_value(value)
        assert result == value

    def test_cast_dict_with_nested_dict(self) -> None:
        """Test casting dict containing nested dict."""
        value = {"outer": {"inner": "value"}, "num": 42}
        result = cast_value(value)
        assert result == value

    def test_cast_dict_with_nested_list(self) -> None:
        """Test casting dict containing nested list."""
        value = {"items": [1, 2, 3], "name": "test"}
        result = cast_value(value)
        assert result == value

    def test_cast_tuple_with_nested_tuple(self) -> None:
        """Test casting tuple containing nested tuple."""
        value = (1, (2, 3), "hello")
        result = cast_value(value)
        assert result == value

    def test_cast_deeply_nested_structure(self) -> None:
        """Test casting deeply nested composite structure."""
        value = {"level1": {"level2": [1, 2, {"level3": "deep"}]}}
        result = cast_value(value)
        assert result == value


class TestCastValuePreservesIdentity:
    """Test that cast_value() preserves value identity/equality."""

    def test_cast_preserves_value_equality(self) -> None:
        """Test that cast_value preserves value equality."""
        original = {"a": 1, "b": [2, 3], "c": (4, 5)}
        casted = cast_value(original)
        assert casted == original

    def test_cast_multiple_calls_are_consistent(self) -> None:
        """Test that multiple calls to cast_value return equal results."""
        value = [1, 2, 3]
        result1 = cast_value(value)
        result2 = cast_value(value)
        assert result1 == result2

    def test_cast_returns_same_reference(self) -> None:
        """Test that cast_value returns the same object reference."""
        value = [1, 2, 3]
        result = cast_value(value)
        # cast() is a no-op at runtime, so it returns the same object
        assert result is value


class TestCastValueEdgeCases:
    """Test cast_value() with edge cases."""

    def test_cast_dict_with_numeric_and_string_keys(self) -> None:
        """Test dict with mixed key types."""
        value = {1: "one", "two": 2, 3.14: "pi"}
        result = cast_value(value)
        assert result == value

    def test_cast_list_with_none_values(self) -> None:
        """Test list containing None values."""
        value = [None, 1, None, "test", None]
        result = cast_value(value)
        assert result == value

    def test_cast_large_list(self) -> None:
        """Test casting large list."""
        value = list(range(1000))
        result = cast_value(value)
        assert result == value

    def test_cast_bytes_empty(self) -> None:
        """Test casting empty bytes."""
        value = b""
        result = cast_value(value)
        assert result == value

    def test_cast_bytes_with_special_chars(self) -> None:
        """Test casting bytes with special characters."""
        value = b"\x00\x01\x02\xff"
        result = cast_value(value)
        assert result == value

    def test_cast_str_with_unicode(self) -> None:
        """Test casting string with unicode characters."""
        value = "Hello 世界 🌍"
        result = cast_value(value)
        assert result == value
