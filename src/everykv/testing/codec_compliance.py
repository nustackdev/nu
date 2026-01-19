"""Abstract compliance test suite for KeyCodecProtocol implementations.

This module provides a test framework for verifying that key codec implementations
correctly implement the KeyCodecProtocol interface. These are compliance tests
that verify roundtrip correctness, lexicographic ordering preservation, and
determinism.

Usage:
    Inherit from KeyCodecCompliance and override the codec fixture:

    ```python
    from everyshape.testing import KeyCodecCompliance


    class TestMyCodec(KeyCodecCompliance):
        @pytest.fixture
        def codec(self):
            return MyKeyCodec()
    ```

Test Coverage:
    - Roundtrip: decode(encode(key)) == key
    - Lexicographic ordering preservation
    - Determinism and stability
    - Error handling for invalid inputs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pytest


if TYPE_CHECKING:
    from everykv.loc.key import Key


class KeyCodecProtocolForTest(Protocol):
    """Protocol for key codec under test."""

    def encode(self, key: Key) -> bytes | str:
        """Encode key."""
        ...

    def decode(self, encoded: bytes | str) -> Key:
        """Decode key."""
        ...


# =============================================================================
# Key Codec Compliance Tests
# =============================================================================


class KeyCodecCompliance:
    """Compliance tests for KeyCodecProtocol implementations.

    Tests roundtrip correctness, ordering preservation, and determinism.
    Subclasses must provide a `codec` fixture.
    """

    @pytest.fixture
    def codec(self) -> KeyCodecProtocolForTest:
        """Override to provide codec implementation."""
        raise NotImplementedError("Subclass must provide codec fixture")

    # ========================================================================
    # Roundtrip Tests
    # ========================================================================

    def test_roundtrip_simple_string_key(self, codec: KeyCodecProtocolForTest) -> None:
        """Simple string-only key round-trips correctly."""
        key = ("users", "alice")
        assert codec.decode(codec.encode(key)) == key

    def test_roundtrip_simple_int_key(self, codec: KeyCodecProtocolForTest) -> None:
        """Simple integer-only key round-trips correctly."""
        key = (42, 100)
        assert codec.decode(codec.encode(key)) == key

    def test_roundtrip_mixed_key(self, codec: KeyCodecProtocolForTest) -> None:
        """Mixed string/int key round-trips correctly."""
        key = ("users", 42, "profile")
        assert codec.decode(codec.encode(key)) == key

    def test_roundtrip_single_string(self, codec: KeyCodecProtocolForTest) -> None:
        """Single string component key round-trips correctly."""
        key = ("single",)
        assert codec.decode(codec.encode(key)) == key

    def test_roundtrip_single_int(self, codec: KeyCodecProtocolForTest) -> None:
        """Single integer component key round-trips correctly."""
        key = (42,)
        assert codec.decode(codec.encode(key)) == key

    def test_roundtrip_long_key(self, codec: KeyCodecProtocolForTest) -> None:
        """Long key with many components round-trips correctly."""
        key = ("a", "b", "c", "d", "e", 1, 2, 3, 4, 5)
        assert codec.decode(codec.encode(key)) == key

    # ========================================================================
    # Ordering Tests
    # ========================================================================

    def test_ordering_prefix_shorter_before_longer(self, codec: KeyCodecProtocolForTest) -> None:
        """Shorter key orders before longer key with same prefix."""
        k1 = ("users", 42)
        k2 = ("users", 42, "profile")
        e1, e2 = codec.encode(k1), codec.encode(k2)
        assert e1 < e2

    def test_ordering_negative_integers(self, codec: KeyCodecProtocolForTest) -> None:
        """Negative integers order correctly."""
        keys = [("x", -100), ("x", -10), ("x", 0), ("x", 10), ("x", 100)]
        encoded = [codec.encode(k) for k in keys]
        assert encoded == sorted(encoded)

    def test_ordering_strings(self, codec: KeyCodecProtocolForTest) -> None:
        """String components order lexicographically."""
        keys = [("a",), ("b",), ("c",)]
        encoded = [codec.encode(k) for k in keys]
        assert encoded == sorted(encoded)

    def test_ordering_sorted_keys_remain_sorted(self, codec: KeyCodecProtocolForTest) -> None:
        """Sorting keys and sorting encoded keys produce same order."""
        keys = [
            ("users", 1),
            ("users", 10),
            ("users", 2),
            ("items", 5),
            ("admin", 0),
        ]

        sorted_keys = sorted(keys)
        encoded_pairs = [(codec.encode(k), k) for k in keys]
        sorted_by_encoded = [k for _, k in sorted(encoded_pairs)]

        assert sorted_keys == sorted_by_encoded

    def test_ordering_zero_boundary(self, codec: KeyCodecProtocolForTest) -> None:
        """Ordering is correct around zero boundary."""
        keys = [(-2,), (-1,), (0,), (1,), (2,)]
        encoded = [codec.encode(k) for k in keys]
        assert encoded == sorted(encoded)

    def test_ordering_string_prefix(self, codec: KeyCodecProtocolForTest) -> None:
        """Shorter string sorts before longer string with same prefix."""
        k1 = ("a",)
        k2 = ("aa",)
        e1, e2 = codec.encode(k1), codec.encode(k2)
        assert k1 < k2
        assert e1 < e2

    def test_ordering_integer_before_string(self, codec: KeyCodecProtocolForTest) -> None:
        """Integers sort before strings (type marker ordering)."""
        k_int = (0,)
        k_str = ("0",)
        e_int, e_str = codec.encode(k_int), codec.encode(k_str)
        assert e_int < e_str

    # ========================================================================
    # Integer Edge Cases
    # ========================================================================

    def test_integer_zero(self, codec: KeyCodecProtocolForTest) -> None:
        """Zero encodes and decodes correctly."""
        key = (0,)
        assert codec.decode(codec.encode(key)) == key

    def test_integer_one(self, codec: KeyCodecProtocolForTest) -> None:
        """One encodes and decodes correctly."""
        key = (1,)
        assert codec.decode(codec.encode(key)) == key

    def test_integer_negative_one(self, codec: KeyCodecProtocolForTest) -> None:
        """Negative one encodes and decodes correctly."""
        key = (-1,)
        assert codec.decode(codec.encode(key)) == key

    # ========================================================================
    # Determinism Tests
    # ========================================================================

    def test_determinism_same_key_same_encoding(self, codec: KeyCodecProtocolForTest) -> None:
        """Same key always produces same encoding."""
        key = ("users", 42, "profile")
        encodings = [codec.encode(key) for _ in range(10)]
        assert all(e == encodings[0] for e in encodings)

    def test_determinism_equivalent_keys(self, codec: KeyCodecProtocolForTest) -> None:
        """Equivalent keys produce same encoding."""
        key1 = ("test", 123)
        key2 = ("test", 123)
        assert codec.encode(key1) == codec.encode(key2)

    def test_determinism_encode_decode_encode(self, codec: KeyCodecProtocolForTest) -> None:
        """encode(decode(encode(k))) == encode(k)."""
        key = ("users", 42, "data")
        encoded1 = codec.encode(key)
        decoded = codec.decode(encoded1)
        encoded2 = codec.encode(decoded)
        assert encoded1 == encoded2

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_error_empty_tuple_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """Empty tuple is rejected."""
        with pytest.raises(Exception):  # EncodeError or similar
            codec.encode(())

    def test_error_none_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """None as key is rejected."""
        with pytest.raises(Exception):
            codec.encode(None)  # type: ignore

    def test_error_list_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """List instead of tuple is rejected."""
        with pytest.raises(Exception):
            codec.encode(["a", "b"])  # type: ignore

    def test_error_float_component_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """Float component is rejected."""
        with pytest.raises(Exception):
            codec.encode((3.14,))  # type: ignore

    def test_error_none_component_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """None component is rejected."""
        with pytest.raises(Exception):
            codec.encode((None,))  # type: ignore

    def test_error_nested_tuple_rejected(self, codec: KeyCodecProtocolForTest) -> None:
        """Nested tuple component is rejected."""
        with pytest.raises(Exception):
            codec.encode((("nested",),))  # type: ignore


# =============================================================================
# Value Codec Compliance Tests
# =============================================================================


class ValueCodecCompliance:
    """Compliance tests for ValueCodecProtocol implementations.

    Tests roundtrip correctness for various value types.
    Subclasses must provide a `value_codec` fixture.
    """

    @pytest.fixture
    def value_codec(self):
        """Override to provide value codec implementation."""
        raise NotImplementedError("Subclass must provide value_codec fixture")

    def test_roundtrip_bytes(self, value_codec) -> None:
        """Bytes value round-trips correctly."""
        value = b"hello world"
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_string(self, value_codec) -> None:
        """String value round-trips correctly."""
        value = "hello world"
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_int(self, value_codec) -> None:
        """Integer value round-trips correctly."""
        value = 42
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_float(self, value_codec) -> None:
        """Float value round-trips correctly."""
        value = 3.14159
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_bool_true(self, value_codec) -> None:
        """Boolean True round-trips correctly."""
        value = True
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_bool_false(self, value_codec) -> None:
        """Boolean False round-trips correctly."""
        value = False
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_none(self, value_codec) -> None:
        """None value round-trips correctly."""
        value = None
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_dict(self, value_codec) -> None:
        """Dict value round-trips correctly."""
        value = {"key": "value", "number": 42}
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_list(self, value_codec) -> None:
        """List value round-trips correctly."""
        value = [1, 2, "three", None]
        assert value_codec.decode(value_codec.encode(value)) == value

    def test_roundtrip_nested(self, value_codec) -> None:
        """Nested structure round-trips correctly."""
        value = {"users": [{"name": "alice", "age": 30}], "count": 1}
        assert value_codec.decode(value_codec.encode(value)) == value
