"""Functional tests for rwtup key codecs.

Tests run against all codec implementations (BinaryKeyCodec, PyBinaryKeyCodec, StringKeyCodec)
using pytest parametrization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import given
from hypothesis import strategies as st


if TYPE_CHECKING:
    from rwtup.protocols import KeyCodec
    from rwtup.types import Key


# ============================================================================
# Test Data Strategies
# ============================================================================


@st.composite
def safe_key(draw: st.DrawFn) -> Key:
    """Generate keys safe for all codecs (intersection of all constraints)."""
    components = draw(
        st.lists(
            st.one_of(
                # Strings: no forbidden chars for StringKeyCodec
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"),
                        blacklist_characters=".[]",
                    ),
                    min_size=1,
                    max_size=50,
                ),
                # Integers: StringKeyCodec has smallest range
                st.integers(min_value=-49999, max_value=49999),
            ),
            min_size=1,
            max_size=5,
        )
    )
    return tuple(components)


# ============================================================================
# Core Functional Tests
# ============================================================================


class TestCodecRoundtrip:
    """Test encode/decode round-trip for all codecs."""

    @given(key=safe_key())
    def test_roundtrip(self, codec: KeyCodec, key: Key) -> None:
        """Encode then decode returns original key."""
        assert codec.decode(codec.encode(key)) == key

    def test_simple_string_key(self, codec: KeyCodec) -> None:
        """Simple string-only key."""
        key = ("users", "alice")
        assert codec.decode(codec.encode(key)) == key

    def test_simple_int_key(self, codec: KeyCodec) -> None:
        """Simple integer-only key."""
        key = (42, 100)
        assert codec.decode(codec.encode(key)) == key

    def test_mixed_key(self, codec: KeyCodec) -> None:
        """Mixed string/int key."""
        key = ("users", 42, "profile")
        assert codec.decode(codec.encode(key)) == key


class TestLexicographicOrdering:
    """Test lexicographic ordering preservation for all codecs."""

    @given(k1=safe_key(), k2=safe_key())
    def test_ordering_preserved(self, codec: KeyCodec, k1: Key, k2: Key) -> None:
        """Lexicographic ordering preserved: k1 < k2 ⟺ encode(k1) < encode(k2)."""
        e1, e2 = codec.encode(k1), codec.encode(k2)

        # Python 3 can't compare tuples with incompatible types (e.g., ('0',) vs (0,))
        # In such cases, the codec still orders them deterministically (int < str via type markers)
        try:
            if k1 < k2:
                assert e1 < e2
            elif k1 > k2:
                assert e1 > e2
            else:
                assert e1 == e2
        except TypeError:
            # Types incomparable - codec still produces deterministic ordering
            # Just verify encoding succeeded
            assert isinstance(e1, (bytes, str))
            assert isinstance(e2, (bytes, str))

    def test_prefix_ordering(self, codec: KeyCodec) -> None:
        """Shorter key orders before longer key with same prefix."""
        k1 = ("users", 42)
        k2 = ("users", 42, "profile")
        e1, e2 = codec.encode(k1), codec.encode(k2)
        assert e1 < e2

    def test_negative_integers(self, codec: KeyCodec) -> None:
        """Negative integers order correctly."""
        keys = [("x", -100), ("x", -10), ("x", 0), ("x", 10), ("x", 100)]
        encoded = [codec.encode(k) for k in keys]
        assert encoded == sorted(encoded)

    def test_string_ordering(self, codec: KeyCodec) -> None:
        """String components order lexicographically."""
        keys = [("a",), ("b",), ("c",)]
        encoded = [codec.encode(k) for k in keys]
        assert encoded == sorted(encoded)

    def test_sorted_keys_remain_sorted(self, codec: KeyCodec) -> None:
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
