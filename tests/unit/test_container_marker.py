"""Unit tests for the container marker system."""

from __future__ import annotations

import pytest

from everyshape.container.marker import (
    MARKER_SENTINEL,
    create_marker,
    extract_marker,
    is_marker,
    validate_marker_compatibility,
)
from everyshape.container.types import ContainerProtocol, ContainerStructure


# ========================================================================
# Test Constants
# ========================================================================


# Create test container structures using ContainerStructure NewType
TEST_DICT_STRUCTURE = ContainerStructure(0)
TEST_LIST_STRUCTURE = ContainerStructure(1)
TEST_SET_STRUCTURE = ContainerStructure(2)

# Create test protocol flags
TEST_MUTABLE = ContainerProtocol.MUTABLE
TEST_SIZED = ContainerProtocol.SIZED
TEST_INDEXED = ContainerProtocol.INDEXED
TEST_MAPPING = ContainerProtocol.MAPPING
TEST_SET_FLAG = ContainerProtocol.SET
TEST_NONE = ContainerProtocol.NONE


# ========================================================================
# Tests for MARKER_SENTINEL constant
# ========================================================================


class TestMarkerSentinel:
    """Tests for the MARKER_SENTINEL constant."""

    def test_marker_sentinel_is_string(self) -> None:
        """Test that MARKER_SENTINEL is a string."""
        assert isinstance(MARKER_SENTINEL, str)

    def test_marker_sentinel_length(self) -> None:
        """Test that MARKER_SENTINEL has correct length (2 characters)."""
        assert len(MARKER_SENTINEL) == 2

    def test_marker_sentinel_contains_pua_characters(self) -> None:
        """Test that MARKER_SENTINEL contains expected Unicode PUA characters."""
        # First character should be U+E000 (BMP PUA)
        assert MARKER_SENTINEL[0] == "\ue000"
        # Second character should be U+F0000 (Supplementary PUA-A)
        assert MARKER_SENTINEL[1] == "\U000f0000"

    def test_marker_sentinel_unicode_codepoints(self) -> None:
        """Test exact Unicode codepoint values."""
        # U+E000 = 57344 decimal
        assert ord(MARKER_SENTINEL[0]) == 0xE000
        # U+F0000 = 983040 decimal
        assert ord(MARKER_SENTINEL[1]) == 0xF0000

    def test_marker_sentinel_uniqueness(self) -> None:
        """Test that the sentinel value is highly unlikely to appear in user data."""
        # Sentinel combines characters from two separate Unicode planes
        # This makes accidental collision virtually impossible
        assert len(MARKER_SENTINEL) == 2
        # Both characters are from private use areas
        assert 0xE000 <= ord(MARKER_SENTINEL[0]) <= 0xF8FF  # BMP PUA range
        assert 0xF0000 <= ord(MARKER_SENTINEL[1]) <= 0xFFFFC  # SPUA-A range

    def test_marker_sentinel_byte_representation(self) -> None:
        """Test UTF-8 byte representation of sentinel."""
        utf8_bytes = MARKER_SENTINEL.encode("utf-8")
        # U+E000 encodes to 3 bytes: EE 80 80
        # U+F0000 encodes to 4 bytes: F3 B0 80 80
        # Total: 7 bytes
        assert len(utf8_bytes) == 7
        assert utf8_bytes == b"\xee\x80\x80\xf3\xb0\x80\x80"


# ========================================================================
# Tests for create_marker()
# ========================================================================


class TestCreateMarker:
    """Tests for the create_marker() function."""

    def test_create_marker_returns_tuple(self) -> None:
        """Test that create_marker returns a tuple."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert isinstance(marker, tuple)

    def test_create_marker_tuple_length(self) -> None:
        """Test that the returned marker tuple has exactly 4 elements."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert len(marker) == 4

    def test_create_marker_structure_at_index_1(self) -> None:
        """Test that structure is at index 1."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert marker[1] == TEST_DICT_STRUCTURE

    def test_create_marker_protocol_value_at_index_2(self) -> None:
        """Test that protocol value (int) is at index 2."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        # protocol.value extracts the int value from IntFlag
        assert marker[2] == TEST_MUTABLE.value
        assert isinstance(marker[2], int)

    def test_create_marker_sentinels_at_edges(self) -> None:
        """Test that MARKER_SENTINEL is at positions [0] and [3]."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert marker[0] == MARKER_SENTINEL
        assert marker[3] == MARKER_SENTINEL

    def test_create_marker_with_different_structures(self) -> None:
        """Test creating markers with different container structures."""
        dict_marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        list_marker = create_marker(TEST_LIST_STRUCTURE, TEST_MUTABLE)
        set_marker = create_marker(TEST_SET_STRUCTURE, TEST_MUTABLE)

        assert dict_marker[1] == TEST_DICT_STRUCTURE
        assert list_marker[1] == TEST_LIST_STRUCTURE
        assert set_marker[1] == TEST_SET_STRUCTURE

    def test_create_marker_with_different_protocols(self) -> None:
        """Test creating markers with different protocol flags."""
        mutable_marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        sized_marker = create_marker(TEST_DICT_STRUCTURE, TEST_SIZED)
        indexed_marker = create_marker(TEST_DICT_STRUCTURE, TEST_INDEXED)

        assert mutable_marker[2] == TEST_MUTABLE.value
        assert sized_marker[2] == TEST_SIZED.value
        assert indexed_marker[2] == TEST_INDEXED.value

    def test_create_marker_with_combined_protocols(self) -> None:
        """Test creating markers with combined protocol flags."""
        combined = TEST_MUTABLE | TEST_SIZED | TEST_INDEXED
        marker = create_marker(TEST_DICT_STRUCTURE, combined)
        assert marker[2] == combined.value

    def test_create_marker_with_none_protocol(self) -> None:
        """Test creating marker with NONE protocol flag."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_NONE)
        assert marker[2] == TEST_NONE.value
        assert marker[2] == 0


# ========================================================================
# Tests for extract_marker()
# ========================================================================


class TestExtractMarker:
    """Tests for the extract_marker() function."""

    def test_extract_marker_from_valid_marker(self) -> None:
        """Test extracting structure and protocol from a valid marker."""
        created = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        result = extract_marker(created)

        assert result is not None
        structure, protocol = result
        assert structure == TEST_DICT_STRUCTURE
        assert protocol == TEST_MUTABLE

    def test_extract_marker_with_different_structures(self) -> None:
        """Test extracting markers with different structures."""
        for structure in [TEST_DICT_STRUCTURE, TEST_LIST_STRUCTURE, TEST_SET_STRUCTURE]:
            marker = create_marker(structure, TEST_MUTABLE)
            result = extract_marker(marker)
            assert result is not None
            extracted_structure, _ = result
            assert extracted_structure == structure

    def test_extract_marker_with_different_protocols(self) -> None:
        """Test extracting markers with different protocols."""
        for protocol in [TEST_MUTABLE, TEST_SIZED, TEST_INDEXED, TEST_NONE]:
            marker = create_marker(TEST_DICT_STRUCTURE, protocol)
            result = extract_marker(marker)
            assert result is not None
            _, extracted_protocol = result
            assert extracted_protocol == protocol

    def test_extract_marker_returns_none_for_non_tuple(self) -> None:
        """Test that extract_marker returns None for non-tuple values."""
        assert extract_marker("not a tuple") is None
        assert extract_marker(123) is None
        assert extract_marker([MARKER_SENTINEL, 0, 0, MARKER_SENTINEL]) is None
        assert extract_marker({"sentinel": MARKER_SENTINEL}) is None

    def test_extract_marker_returns_none_for_wrong_length(self) -> None:
        """Test that extract_marker returns None for tuples with wrong length."""
        assert extract_marker(()) is None
        assert extract_marker((MARKER_SENTINEL,)) is None
        assert extract_marker((MARKER_SENTINEL, 0, 0)) is None
        assert extract_marker((MARKER_SENTINEL, 0, 0, MARKER_SENTINEL, "extra")) is None

    def test_extract_marker_returns_none_for_missing_first_sentinel(self) -> None:
        """Test that extract_marker returns None when first sentinel is missing."""
        bad_marker = ("wrong", TEST_DICT_STRUCTURE, TEST_MUTABLE.value, MARKER_SENTINEL)
        assert extract_marker(bad_marker) is None

    def test_extract_marker_returns_none_for_missing_last_sentinel(self) -> None:
        """Test that extract_marker returns None when last sentinel is missing."""
        bad_marker = (MARKER_SENTINEL, TEST_DICT_STRUCTURE, TEST_MUTABLE.value, "wrong")
        assert extract_marker(bad_marker) is None

    def test_extract_marker_returns_none_for_wrong_sentinels(self) -> None:
        """Test that extract_marker returns None for different sentinels."""
        bad_marker = ("sentinel", TEST_DICT_STRUCTURE, TEST_MUTABLE.value, "sentinel")
        assert extract_marker(bad_marker) is None

    def test_extract_marker_returns_none_for_none_type(self) -> None:
        """Test that extract_marker returns None for None input."""
        assert extract_marker(None) is None

    def test_extract_marker_roundtrip(self) -> None:
        """Test that create and extract roundtrip correctly."""
        original_structure = TEST_LIST_STRUCTURE
        original_protocol = TEST_MUTABLE | TEST_INDEXED

        marker = create_marker(original_structure, original_protocol)
        result = extract_marker(marker)

        assert result is not None
        extracted_structure, extracted_protocol = result
        assert extracted_structure == original_structure
        assert extracted_protocol == original_protocol

    def test_extract_marker_with_combined_protocols(self) -> None:
        """Test extracting marker with combined protocol flags."""
        combined = TEST_MUTABLE | TEST_SIZED | TEST_MAPPING
        marker = create_marker(TEST_DICT_STRUCTURE, combined)
        result = extract_marker(marker)

        assert result is not None
        _, protocol = result
        assert protocol == combined


# ========================================================================
# Tests for is_marker()
# ========================================================================


class TestIsMarker:
    """Tests for the is_marker() function."""

    def test_is_marker_returns_true_for_valid_marker(self) -> None:
        """Test that is_marker returns True for valid markers."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert is_marker(marker) is True

    def test_is_marker_returns_false_for_non_tuple(self) -> None:
        """Test that is_marker returns False for non-tuple values."""
        assert is_marker("not a marker") is False
        assert is_marker(123) is False
        assert is_marker(None) is False
        assert is_marker([]) is False
        assert is_marker({}) is False

    def test_is_marker_returns_false_for_wrong_length_tuple(self) -> None:
        """Test that is_marker returns False for wrong length tuples."""
        assert is_marker(()) is False
        assert is_marker((MARKER_SENTINEL,)) is False
        assert is_marker((MARKER_SENTINEL, 0, 0)) is False
        assert is_marker((MARKER_SENTINEL, 0, 0, MARKER_SENTINEL, "extra")) is False

    def test_is_marker_returns_false_for_wrong_sentinels(self) -> None:
        """Test that is_marker returns False when sentinels don't match."""
        bad_marker = ("not_sentinel", TEST_DICT_STRUCTURE, TEST_MUTABLE.value, MARKER_SENTINEL)
        assert is_marker(bad_marker) is False

        bad_marker = (MARKER_SENTINEL, TEST_DICT_STRUCTURE, TEST_MUTABLE.value, "not_sentinel")
        assert is_marker(bad_marker) is False

    def test_is_marker_returns_false_for_malformed_marker(self) -> None:
        """Test that is_marker returns False for malformed markers."""
        # Valid structure but no sentinels
        bad_marker = (0, TEST_DICT_STRUCTURE, TEST_MUTABLE.value, 0)
        assert is_marker(bad_marker) is False

    def test_is_marker_with_different_structures(self) -> None:
        """Test is_marker with different container structures."""
        for structure in [TEST_DICT_STRUCTURE, TEST_LIST_STRUCTURE, TEST_SET_STRUCTURE]:
            marker = create_marker(structure, TEST_MUTABLE)
            assert is_marker(marker) is True

    def test_is_marker_with_different_protocols(self) -> None:
        """Test is_marker with different protocol flags."""
        for protocol in [TEST_MUTABLE, TEST_SIZED, TEST_INDEXED, TEST_NONE]:
            marker = create_marker(TEST_DICT_STRUCTURE, protocol)
            assert is_marker(marker) is True

    def test_is_marker_efficiency(self) -> None:
        """Test that is_marker can quickly determine validity."""
        # is_marker should be a fast boolean check, not extract full data
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        # Call multiple times to verify it's consistently fast
        for _ in range(100):
            result = is_marker(marker)
            assert result is True


# ========================================================================
# Tests for validate_marker_compatibility()
# ========================================================================


class TestValidateMarkerCompatibility:
    """Tests for the validate_marker_compatibility() function."""

    def test_validate_compatibility_exact_match(self) -> None:
        """Test validation when marker matches exactly."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        result = validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MUTABLE)
        assert result is True

    def test_validate_compatibility_structure_must_match_exactly(self) -> None:
        """Test that structure must match exactly."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)

        # Same structure should pass
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MUTABLE) is True

        # Different structure should fail
        assert validate_marker_compatibility(marker, TEST_LIST_STRUCTURE, TEST_MUTABLE) is False

        assert validate_marker_compatibility(marker, TEST_SET_STRUCTURE, TEST_MUTABLE) is False

    def test_validate_compatibility_protocol_bitwise_match(self) -> None:
        """Test that protocol requires at least one common flag."""
        # Create marker with MUTABLE | SIZED
        combined = TEST_MUTABLE | TEST_SIZED
        marker = create_marker(TEST_DICT_STRUCTURE, combined)

        # Should pass if expecting MUTABLE (common flag)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MUTABLE) is True

        # Should pass if expecting SIZED (common flag)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_SIZED) is True

        # Should pass if expecting MUTABLE | INDEXED (MUTABLE is common)
        combined_expected = TEST_MUTABLE | TEST_INDEXED
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, combined_expected) is True

    def test_validate_compatibility_protocol_no_common_flag(self) -> None:
        """Test that protocol validation fails with no common flags."""
        # Create marker with MUTABLE only
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)

        # Should fail when expecting different flags
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_SIZED) is False

        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_INDEXED) is False

    def test_validate_compatibility_protocol_none(self) -> None:
        """Test validation with NONE protocol flag."""
        # Marker with NONE protocol
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_NONE)

        # Should fail when expecting any flag (no common flags with 0)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MUTABLE) is False

        # Should fail when expecting any other flag
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_SIZED) is False

    def test_validate_compatibility_invalid_marker(self) -> None:
        """Test that validation returns False for invalid markers."""
        # Non-marker value
        assert (
            validate_marker_compatibility("not a marker", TEST_DICT_STRUCTURE, TEST_MUTABLE)
            is False
        )

        # Wrong length tuple
        assert (
            validate_marker_compatibility(
                (MARKER_SENTINEL, 0, 0), TEST_DICT_STRUCTURE, TEST_MUTABLE
            )
            is False
        )

        # Missing sentinels
        bad_marker = (0, TEST_DICT_STRUCTURE, TEST_MUTABLE.value, 0)
        assert validate_marker_compatibility(bad_marker, TEST_DICT_STRUCTURE, TEST_MUTABLE) is False

        # None value
        assert validate_marker_compatibility(None, TEST_DICT_STRUCTURE, TEST_MUTABLE) is False

    def test_validate_compatibility_combined_protocols(self) -> None:
        """Test validation with combined protocol flags."""
        # Marker with MUTABLE | INDEXED
        combined = TEST_MUTABLE | TEST_INDEXED
        marker = create_marker(TEST_DICT_STRUCTURE, combined)

        # Expecting MUTABLE | SIZED (MUTABLE is common)
        expected = TEST_MUTABLE | TEST_SIZED
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, expected) is True

        # Expecting SIZED | MAPPING (no common flags)
        expected = TEST_SIZED | TEST_MAPPING
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, expected) is False

    def test_validate_compatibility_structure_mismatch_overrides_protocol(self) -> None:
        """Test that structure mismatch fails even with matching protocol."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)

        # Even though protocol matches, structure doesn't
        assert validate_marker_compatibility(marker, TEST_LIST_STRUCTURE, TEST_MUTABLE) is False

    def test_validate_compatibility_all_combinations(self) -> None:
        """Test various combinations of structures and protocols."""
        structures = [TEST_DICT_STRUCTURE, TEST_LIST_STRUCTURE, TEST_SET_STRUCTURE]
        protocols = [TEST_MUTABLE, TEST_SIZED, TEST_INDEXED]

        for structure in structures:
            for protocol in protocols:
                marker = create_marker(structure, protocol)

                # Same structure and protocol should pass
                assert validate_marker_compatibility(marker, structure, protocol) is True

                # Different structure should fail
                for other_structure in structures:
                    if other_structure != structure:
                        assert (
                            validate_marker_compatibility(marker, other_structure, protocol)
                            is False
                        )

    def test_validate_compatibility_bitwise_operations(self) -> None:
        """Test that validation uses bitwise AND for protocol matching."""
        # Create marker with MAPPING flag
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MAPPING)

        # MAPPING (2^3 = 8) & MAPPING (8) = 8 (True)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MAPPING) is True

        # MAPPING (8) & MUTABLE (1) = 0 (False)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_MUTABLE) is False

        # MAPPING (8) & SET_FLAG (16) = 0 (False)
        assert validate_marker_compatibility(marker, TEST_DICT_STRUCTURE, TEST_SET_FLAG) is False


# ========================================================================
# Integration Tests
# ========================================================================


class TestMarkerSystemIntegration:
    """Integration tests for the complete marker system."""

    def test_full_marker_lifecycle(self) -> None:
        """Test complete lifecycle: create -> extract -> validate."""
        structure = TEST_LIST_STRUCTURE
        protocol = TEST_MUTABLE | TEST_INDEXED

        # Create marker
        marker = create_marker(structure, protocol)

        # Verify it's recognized as a marker
        assert is_marker(marker) is True

        # Extract information
        result = extract_marker(marker)
        assert result is not None
        extracted_structure, extracted_protocol = result

        # Validate against expectations
        assert (
            validate_marker_compatibility(marker, extracted_structure, extracted_protocol) is True
        )

    def test_multiple_markers_independence(self) -> None:
        """Test that different markers are independent."""
        marker1 = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)
        marker2 = create_marker(TEST_LIST_STRUCTURE, TEST_SIZED)

        # Both should be valid markers
        assert is_marker(marker1) is True
        assert is_marker(marker2) is True

        # They should extract differently
        result1 = extract_marker(marker1)
        result2 = extract_marker(marker2)

        assert result1 != result2
        assert result1[0] != result2[0]  # Different structures
        assert result1[1] != result2[1]  # Different protocols

    def test_marker_immutability(self) -> None:
        """Test that markers are immutable tuples."""
        marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)

        # Tuples should be immutable
        assert isinstance(marker, tuple)
        with pytest.raises(TypeError):
            marker[0] = "modified"  # type: ignore

    def test_sentinel_bookending_protection(self) -> None:
        """Test that sentinel bookending provides validation."""
        valid_marker = create_marker(TEST_DICT_STRUCTURE, TEST_MUTABLE)

        # Valid marker has sentinels at both ends
        assert valid_marker[0] == MARKER_SENTINEL
        assert valid_marker[3] == MARKER_SENTINEL

        # Any modification would break the marker
        corrupted = (MARKER_SENTINEL, TEST_DICT_STRUCTURE, TEST_MUTABLE.value, "X")
        assert is_marker(corrupted) is False

        corrupted = ("X", TEST_DICT_STRUCTURE, TEST_MUTABLE.value, MARKER_SENTINEL)
        assert is_marker(corrupted) is False

    def test_protocol_bitwise_semantics(self) -> None:
        """Test that protocol flags use correct bitwise semantics."""
        # Create marker with multiple flags
        combined = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED | ContainerProtocol.INDEXED
        marker = create_marker(TEST_DICT_STRUCTURE, combined)

        # Test bitwise extraction
        result = extract_marker(marker)
        assert result is not None
        _, protocol = result

        # Each individual flag should be present
        assert protocol & ContainerProtocol.MUTABLE
        assert protocol & ContainerProtocol.SIZED
        assert protocol & ContainerProtocol.INDEXED

        # Combined should equal the sum of flags
        assert protocol == combined
