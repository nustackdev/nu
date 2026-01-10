"""Unit tests for the storage codec module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

from everyshape.loc.key_nav import create_key
from everyshape.storage.codec import Codec


if TYPE_CHECKING:
    from everyshape.types import Value


# Test constants
TEST_KEY = create_key("test", "key")
TEST_ENCODED_KEY = b"encoded_key"
TEST_VALUE = {"test": "data"}
TEST_ENCODED_VALUE = b"encoded_value"


# Mock implementations for testing
class MockKeyCodec:
    """Mock implementation of KeyCodecProtocol."""

    def __init__(self) -> None:
        """Initialize mock key codec."""
        self.encode = Mock(return_value=TEST_ENCODED_KEY)
        self.decode = Mock(return_value=TEST_KEY)


class MockValueCodec:
    """Mock implementation of ValueCodecProtocol."""

    def __init__(self) -> None:
        """Initialize mock value codec."""
        self.encode = Mock(return_value=TEST_ENCODED_VALUE)
        self.decode = Mock(return_value={"key": "value"})


class SimpleKeyCodec:
    """Simple working implementation of KeyCodecProtocol for testing."""

    def encode(self, k: Any) -> bytes:
        """Encode a key to bytes."""
        # k is a tuple (Key type alias)
        return str(k).encode("utf-8")

    def decode(self, encoded: bytes) -> Any:
        """Decode bytes to a key."""
        # Return a key (tuple)
        key_str = encoded.decode("utf-8")
        # Parse the string representation of tuple back
        import ast

        return ast.literal_eval(key_str)


class SimpleValueCodec:
    """Simple working implementation of ValueCodecProtocol for testing."""

    def encode(self, value: Value) -> bytes:
        """Encode a value to bytes."""
        import json

        return json.dumps(value).encode("utf-8")

    def decode(self, encoded: bytes) -> Value:
        """Decode bytes to a value."""
        import json

        return json.loads(encoded.decode("utf-8"))


class TestCodecInitialization:
    """Tests for Codec class initialization."""

    def test_codec_init_creates_instances(self) -> None:
        """Test that Codec initialization creates instances of key and value codecs."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        assert codec.key_codec is not None
        assert codec.value_codec is not None
        assert isinstance(codec.key_codec, SimpleKeyCodec)
        assert isinstance(codec.value_codec, SimpleValueCodec)

    def test_codec_init_sets_function_references(self) -> None:
        """Test that Codec initialization sets up direct function references."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        # Check that function references are set
        assert codec.encode_key is not None
        assert codec.decode_key is not None
        assert codec.encode_value is not None
        assert codec.decode_value is not None

    def test_codec_function_references_are_callable(self) -> None:
        """Test that all function references are callable."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        assert callable(codec.encode_key)
        assert callable(codec.decode_key)
        assert callable(codec.encode_value)
        assert callable(codec.decode_value)

    def test_codec_has_all_required_methods(self) -> None:
        """Test that Codec has all required methods as attributes."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        # All methods should exist as callable attributes
        assert hasattr(codec, "encode_key")
        assert hasattr(codec, "decode_key")
        assert hasattr(codec, "encode_value")
        assert hasattr(codec, "decode_value")


class TestCodecDelegation:
    """Tests for Codec delegation to key and value codecs."""

    def test_codec_delegates_encode_key_to_key_codec(self) -> None:
        """Test that encode_key delegates to key_codec.encode."""
        codec = Codec(MockKeyCodec, MockValueCodec)
        test_key = TEST_KEY

        # Call encode_key method
        result = codec.encode_key(test_key)

        # Verify the mock was called
        codec.key_codec.encode.assert_called_once_with(test_key)
        assert result == TEST_ENCODED_KEY

    def test_codec_delegates_decode_key_to_key_codec(self) -> None:
        """Test that decode_key delegates to key_codec.decode."""
        codec = Codec(MockKeyCodec, MockValueCodec)
        encoded_key = TEST_ENCODED_KEY

        # Call decode_key method
        result = codec.decode_key(encoded_key)

        # Verify the mock was called
        codec.key_codec.decode.assert_called_once_with(encoded_key)
        assert result == TEST_KEY

    def test_codec_delegates_encode_value_to_value_codec(self) -> None:
        """Test that encode_value delegates to value_codec.encode."""
        codec = Codec(MockKeyCodec, MockValueCodec)
        test_value = TEST_VALUE

        # Call encode_value method
        result = codec.encode_value(test_value)

        # Verify the mock was called
        codec.value_codec.encode.assert_called_once_with(test_value)
        assert result == TEST_ENCODED_VALUE

    def test_codec_delegates_decode_value_to_value_codec(self) -> None:
        """Test that decode_value delegates to value_codec.decode."""
        codec = Codec(MockKeyCodec, MockValueCodec)
        encoded_value = TEST_ENCODED_VALUE

        # Call decode_value method
        result = codec.decode_value(encoded_value)

        # Verify the mock was called
        codec.value_codec.decode.assert_called_once_with(encoded_value)
        assert result == {"key": "value"}


class TestCodecFunctionReferences:
    """Tests for Codec function reference setup and behavior."""

    def test_encode_key_method_works(self) -> None:
        """Test that encode_key method works correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        test_key = create_key("my", "key")

        result = codec.encode_key(test_key)

        assert isinstance(result, bytes)
        assert result == str(test_key).encode("utf-8")

    def test_decode_key_method_works(self) -> None:
        """Test that decode_key method works correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        test_key = create_key("my", "key")
        encoded_key = str(test_key).encode("utf-8")

        result = codec.decode_key(encoded_key)

        assert result == test_key

    def test_encode_value_method_works(self) -> None:
        """Test that encode_value method works correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        test_value = {"name": "test", "count": 42}

        result = codec.encode_value(test_value)

        assert isinstance(result, bytes)
        # Verify it can be decoded back
        import json

        decoded = json.loads(result.decode("utf-8"))
        assert decoded == test_value

    def test_decode_value_method_works(self) -> None:
        """Test that decode_value method works correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        test_value = {"name": "test", "count": 42}
        import json

        encoded_value = json.dumps(test_value).encode("utf-8")

        result = codec.decode_value(encoded_value)

        assert result == test_value

    def test_codec_methods_are_different(self) -> None:
        """Test that codec has different methods for different operations."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        # Different methods should be callable
        assert callable(codec.encode_key)
        assert callable(codec.decode_key)
        assert callable(codec.encode_value)
        assert callable(codec.decode_value)

    def test_multiple_codec_instances_are_independent(self) -> None:
        """Test that multiple Codec instances have independent codec instances."""
        codec1 = Codec(SimpleKeyCodec, SimpleValueCodec)
        codec2 = Codec(SimpleKeyCodec, SimpleValueCodec)

        # They should not share the same codec instances
        assert codec1.key_codec is not codec2.key_codec
        assert codec1.value_codec is not codec2.value_codec


class TestCodecProtocolConformance:
    """Tests for protocol conformance using isinstance checks."""

    def test_codec_conforms_to_codec_protocol(self) -> None:
        """Test that Codec instance conforms to CodecProtocol."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        # Runtime check that codec has all required methods from CodecProtocol
        assert hasattr(codec, "encode_key")
        assert hasattr(codec, "decode_key")
        assert hasattr(codec, "encode_value")
        assert hasattr(codec, "decode_value")

    def test_codec_has_all_codec_protocol_methods(self) -> None:
        """Test that Codec has all methods defined by CodecProtocol."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)

        codec_protocol_methods = ["encode_key", "decode_key", "encode_value", "decode_value"]

        for method_name in codec_protocol_methods:
            assert hasattr(codec, method_name), f"Codec missing {method_name} method"
            method = getattr(codec, method_name)
            assert callable(method), f"{method_name} is not callable"

    def test_key_codec_conforms_to_key_codec_protocol(self) -> None:
        """Test that key codec instance conforms to KeyCodecProtocol."""
        key_codec = SimpleKeyCodec()

        # Runtime check that key_codec has required methods
        assert hasattr(key_codec, "encode")
        assert hasattr(key_codec, "decode")
        assert callable(key_codec.encode)
        assert callable(key_codec.decode)

    def test_value_codec_conforms_to_value_codec_protocol(self) -> None:
        """Test that value codec instance conforms to ValueCodecProtocol."""
        value_codec = SimpleValueCodec()

        # Runtime check that value_codec has required methods
        assert hasattr(value_codec, "encode")
        assert hasattr(value_codec, "decode")
        assert callable(value_codec.encode)
        assert callable(value_codec.decode)

    def test_mock_key_codec_conforms_to_protocol(self) -> None:
        """Test that mock key codec conforms to KeyCodecProtocol."""
        # Create a fresh instance for this test to avoid cross-test mock state issues
        mock_codec = MockKeyCodec()

        assert hasattr(mock_codec, "encode")
        assert hasattr(mock_codec, "decode")
        assert callable(mock_codec.encode)
        assert callable(mock_codec.decode)

    def test_mock_value_codec_conforms_to_protocol(self) -> None:
        """Test that mock value codec conforms to ValueCodecProtocol."""
        mock_codec = MockValueCodec()

        assert hasattr(mock_codec, "encode")
        assert hasattr(mock_codec, "decode")
        assert callable(mock_codec.encode)
        assert callable(mock_codec.decode)


class TestCodecRoundTrip:
    """Tests for round-trip encoding and decoding with Codec."""

    def test_key_round_trip(self) -> None:
        """Test that keys can be encoded and decoded correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        original_key = create_key("test", "key", "123")

        encoded = codec.encode_key(original_key)
        decoded = codec.decode_key(encoded)

        assert decoded == original_key

    def test_value_round_trip(self) -> None:
        """Test that values can be encoded and decoded correctly."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        original_value = {"name": "test", "count": 42, "nested": {"data": True}}

        encoded = codec.encode_value(original_value)
        decoded = codec.decode_value(encoded)

        assert decoded == original_value

    def test_multiple_key_round_trips(self) -> None:
        """Test multiple keys can be encoded and decoded."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        keys = [create_key("key", f"item_{i}") for i in range(5)]

        for original_key in keys:
            encoded = codec.encode_key(original_key)
            decoded = codec.decode_key(encoded)
            assert decoded == original_key

    def test_multiple_value_round_trips(self) -> None:
        """Test multiple values can be encoded and decoded."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        values = [{"id": i, "data": f"value_{i}"} for i in range(5)]

        for original_value in values:
            encoded = codec.encode_value(original_value)
            decoded = codec.decode_value(encoded)
            assert decoded == original_value


class TestCodecIntegration:
    """Integration tests for Codec with key and value codecs."""

    def test_codec_with_custom_key_codec(self) -> None:
        """Test Codec works with custom key codec."""

        class CustomKeyCodec:
            def encode(self, k: Any) -> str:
                return f"KEY:{k}"

            def decode(self, encoded: str) -> Any:
                # Return as string since we're testing custom encoding
                return encoded.replace("KEY:", "")

        codec = Codec(CustomKeyCodec, SimpleValueCodec)
        test_key = "custom_key"

        encoded = codec.encode_key(test_key)
        assert encoded == "KEY:custom_key"

        decoded = codec.decode_key(encoded)
        assert decoded == test_key

    def test_codec_with_custom_value_codec(self) -> None:
        """Test Codec works with custom value codec."""

        class CustomValueCodec:
            def encode(self, value: Value) -> str:
                return f"VALUE:{value}"

            def decode(self, encoded: str) -> Value:
                return encoded.replace("VALUE:", "")

        codec = Codec(SimpleKeyCodec, CustomValueCodec)
        test_value = "test_data"

        encoded = codec.encode_value(test_value)
        assert encoded == "VALUE:test_data"

        decoded = codec.decode_value(encoded)
        assert decoded == test_value

    def test_codec_independent_from_codecs_state(self) -> None:
        """Test that Codec instances don't share state."""
        codec1 = Codec(SimpleKeyCodec, SimpleValueCodec)
        codec2 = Codec(SimpleKeyCodec, SimpleValueCodec)

        key1 = create_key("key", "1")
        key2 = create_key("key", "2")

        encoded1 = codec1.encode_key(key1)
        encoded2 = codec2.encode_key(key2)

        assert encoded1 != encoded2
        assert codec1.decode_key(encoded1) == key1
        assert codec2.decode_key(encoded2) == key2


class TestCodecEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_codec_with_root_only_key(self) -> None:
        """Test Codec with root-only key."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        root_key = create_key()

        encoded = codec.encode_key(root_key)
        decoded = codec.decode_key(encoded)

        assert decoded == root_key

    def test_codec_with_many_segments_in_key(self) -> None:
        """Test Codec with key containing many segments."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        deep_key = create_key("a", "b", "c", "d", "e", "f", "g")

        encoded = codec.encode_key(deep_key)
        decoded = codec.decode_key(encoded)

        assert decoded == deep_key

    def test_codec_with_empty_value(self) -> None:
        """Test Codec with empty value dictionary."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        empty_value: Value = {}

        encoded = codec.encode_value(empty_value)
        decoded = codec.decode_value(encoded)

        assert decoded == empty_value

    def test_codec_with_complex_nested_value(self) -> None:
        """Test Codec with complex nested value."""
        codec = Codec(SimpleKeyCodec, SimpleValueCodec)
        complex_value: Value = {
            "level1": {
                "level2": {
                    "level3": [1, 2, 3, {"nested": "value"}],
                },
                "array": [1, "two", 3.0, True, None],
            },
            "numbers": [1, 2.5, -3],
            "strings": ["hello", "world", ""],
        }

        encoded = codec.encode_value(complex_value)
        decoded = codec.decode_value(encoded)

        assert decoded == complex_value

    def test_codec_methods_called_correctly_with_mocks(self) -> None:
        """Test that codec methods are called correctly with mock codecs."""
        codec = Codec(MockKeyCodec, MockValueCodec)

        test_key = TEST_KEY
        test_value = TEST_VALUE

        # Call the methods
        codec.encode_key(test_key)
        codec.encode_value(test_value)

        # Verify the underlying codec methods were called
        codec.key_codec.encode.assert_called_with(test_key)
        codec.value_codec.encode.assert_called_with(test_value)
