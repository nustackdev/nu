"""Unit tests for storage filters in everyshape.storage.filter."""

from __future__ import annotations

import pytest

from everyshape.storage.filter import (
    WILDCARD,
    And,
    Filter,
    LengthFilter,
    Or,
    PassAll,
    PassNone,
    PrefixFilter,
    SuffixFilter,
    WildcardFilter,
)


# =============================================================================
# PrefixFilter Tests
# =============================================================================


class TestPrefixFilter:
    """Tests for PrefixFilter."""

    def test_matches_with_exact_prefix(self) -> None:
        """Test matching key with exact prefix."""
        f = PrefixFilter(prefix=("users",))
        assert f.matches(("users",))

    def test_matches_with_longer_key(self) -> None:
        """Test matching longer key with matching prefix."""
        f = PrefixFilter(prefix=("users",))
        assert f.matches(("users", "alice"))
        assert f.matches(("users", "alice", "profile"))

    def test_no_match_different_prefix(self) -> None:
        """Test non-matching key with different prefix."""
        f = PrefixFilter(prefix=("users",))
        assert not f.matches(("posts",))
        assert not f.matches(("admin",))

    def test_no_match_shorter_key(self) -> None:
        """Test key shorter than prefix does not match."""
        f = PrefixFilter(prefix=("users", "alice"))
        assert not f.matches(("users",))
        assert not f.matches(())

    def test_empty_prefix_matches_all(self) -> None:
        """Test empty prefix matches all keys."""
        f = PrefixFilter(prefix=())
        assert f.matches(())
        assert f.matches(("users",))
        assert f.matches(("users", "alice"))
        assert f.matches(("a", "b", "c", "d"))

    def test_multi_segment_prefix(self) -> None:
        """Test prefix with multiple segments."""
        f = PrefixFilter(prefix=("users", "alice"))
        assert f.matches(("users", "alice"))
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("users", "bob"))
        assert not f.matches(("users",))

    def test_integer_segments_in_key(self) -> None:
        """Test prefix matching with integer segments."""
        f = PrefixFilter(prefix=("data", 1))
        assert f.matches(("data", 1))
        assert f.matches(("data", 1, "value"))
        assert not f.matches(("data", 2))
        assert not f.matches(("data", "1"))

    def test_prefix_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same prefix."""
        f1 = PrefixFilter(prefix=("users",))
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_prefix_filter_equality_same_prefix(self) -> None:
        """Test equality for filters with same prefix."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("users",))
        assert f1 == f2

    def test_prefix_filter_inequality_different_prefix(self) -> None:
        """Test inequality for filters with different prefixes."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        assert f1 != f2

    def test_prefix_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = PrefixFilter(prefix=("users",))
        assert f != "prefix_users"
        assert f != ("users",)
        assert f.__eq__(None) == NotImplemented

    def test_prefix_filter_in_set(self) -> None:
        """Test prefix filter can be used in sets."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        f3 = PrefixFilter(prefix=("users",))
        filters = {f1, f2, f3}
        assert len(filters) == 2
        assert f1 in filters

    def test_prefix_filter_as_dict_key(self) -> None:
        """Test prefix filter can be used as dict key."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("users",))
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# SuffixFilter Tests
# =============================================================================


class TestSuffixFilter:
    """Tests for SuffixFilter."""

    def test_matches_with_exact_suffix(self) -> None:
        """Test matching key with exact suffix."""
        f = SuffixFilter(suffix=("profile",))
        assert f.matches(("profile",))

    def test_matches_with_longer_key(self) -> None:
        """Test matching longer key with matching suffix."""
        f = SuffixFilter(suffix=("profile",))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("posts", "123", "profile"))

    def test_no_match_different_suffix(self) -> None:
        """Test non-matching key with different suffix."""
        f = SuffixFilter(suffix=("profile",))
        assert not f.matches(("settings",))
        assert not f.matches(("users", "alice"))

    def test_no_match_shorter_key(self) -> None:
        """Test key shorter than suffix does not match."""
        f = SuffixFilter(suffix=("alice", "profile"))
        assert not f.matches(("profile",))
        assert not f.matches(())

    def test_empty_suffix_matches_all(self) -> None:
        """Test empty suffix matches all keys."""
        f = SuffixFilter(suffix=())
        assert f.matches(())
        assert f.matches(("users",))
        assert f.matches(("a", "b", "c"))

    def test_multi_segment_suffix(self) -> None:
        """Test suffix with multiple segments."""
        f = SuffixFilter(suffix=("alice", "profile"))
        assert f.matches(("alice", "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("users", "alice"))
        assert f.matches(("bob", "alice", "profile"))

    def test_integer_segments_in_key(self) -> None:
        """Test suffix matching with integer segments."""
        f = SuffixFilter(suffix=(1, "value"))
        assert f.matches((1, "value"))
        assert f.matches(("data", 1, "value"))
        assert not f.matches((2, "value"))

    def test_suffix_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same suffix."""
        f1 = SuffixFilter(suffix=("profile",))
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_suffix_filter_equality_same_suffix(self) -> None:
        """Test equality for filters with same suffix."""
        f1 = SuffixFilter(suffix=("profile",))
        f2 = SuffixFilter(suffix=("profile",))
        assert f1 == f2

    def test_suffix_filter_inequality_different_suffix(self) -> None:
        """Test inequality for filters with different suffixes."""
        f1 = SuffixFilter(suffix=("profile",))
        f2 = SuffixFilter(suffix=("settings",))
        assert f1 != f2

    def test_suffix_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = SuffixFilter(suffix=("profile",))
        assert f != "profile"
        assert f != ("profile",)
        assert f.__eq__(None) == NotImplemented

    def test_suffix_filter_in_set(self) -> None:
        """Test suffix filter can be used in sets."""
        f1 = SuffixFilter(suffix=("profile",))
        f2 = SuffixFilter(suffix=("settings",))
        f3 = SuffixFilter(suffix=("profile",))
        filters = {f1, f2, f3}
        assert len(filters) == 2

    def test_suffix_filter_as_dict_key(self) -> None:
        """Test suffix filter can be used as dict key."""
        f1 = SuffixFilter(suffix=("profile",))
        f2 = SuffixFilter(suffix=("profile",))
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# WildcardFilter Tests
# =============================================================================


class TestWildcardFilter:
    """Tests for WildcardFilter."""

    def test_matches_exact_pattern(self) -> None:
        """Test matching exact pattern with no wildcards."""
        f = WildcardFilter(pattern=("users", "alice", "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("users", "bob", "profile"))

    def test_matches_with_wildcard_in_middle(self) -> None:
        """Test wildcard matching in middle position."""
        f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("users", "bob", "profile"))
        assert f.matches(("users", "123", "profile"))
        assert not f.matches(("users", "alice", "settings"))

    def test_matches_with_wildcard_at_start(self) -> None:
        """Test wildcard matching at start position."""
        f = WildcardFilter(pattern=(WILDCARD, "alice", "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("admin", "alice", "profile"))
        assert not f.matches(("users", "bob", "profile"))

    def test_matches_with_wildcard_at_end(self) -> None:
        """Test wildcard matching at end position."""
        f = WildcardFilter(pattern=("users", "alice", WILDCARD))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("users", "alice", "settings"))
        assert not f.matches(("users", "bob", "profile"))

    def test_matches_multiple_wildcards(self) -> None:
        """Test multiple wildcards in pattern."""
        f = WildcardFilter(pattern=(WILDCARD, WILDCARD, "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("admin", "bob", "profile"))
        assert f.matches(("a", "b", "profile"))
        assert not f.matches(("users", "alice", "settings"))

    def test_no_match_length_mismatch(self) -> None:
        """Test length mismatch prevents matching."""
        f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        assert not f.matches(("users", "alice"))
        assert not f.matches(("users", "alice", "profile", "extra"))
        assert not f.matches(())

    def test_wildcard_matches_integer_segments(self) -> None:
        """Test wildcard can match integer segments."""
        f = WildcardFilter(pattern=("data", WILDCARD, "value"))
        assert f.matches(("data", 1, "value"))
        assert f.matches(("data", "key", "value"))
        assert f.matches(("data", 999, "value"))

    def test_all_wildcards_pattern(self) -> None:
        """Test pattern with all wildcards."""
        f = WildcardFilter(pattern=(WILDCARD, WILDCARD, WILDCARD))
        assert f.matches(("a", "b", "c"))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("x", "y", "z"))
        assert not f.matches(("a", "b"))
        assert not f.matches(("a", "b", "c", "d"))

    def test_wildcard_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same pattern."""
        f1 = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_wildcard_filter_equality_same_pattern(self) -> None:
        """Test equality for filters with same pattern."""
        f1 = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        f2 = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        assert f1 == f2

    def test_wildcard_filter_inequality_different_pattern(self) -> None:
        """Test inequality for filters with different patterns."""
        f1 = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        f2 = WildcardFilter(pattern=("users", WILDCARD, "settings"))
        assert f1 != f2

    def test_wildcard_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = WildcardFilter(pattern=("users", WILDCARD))
        assert f != ("users", WILDCARD)
        assert f.__eq__(None) == NotImplemented

    def test_wildcard_filter_in_set(self) -> None:
        """Test wildcard filter can be used in sets."""
        f1 = WildcardFilter(pattern=("users", WILDCARD))
        f2 = WildcardFilter(pattern=("posts", WILDCARD))
        f3 = WildcardFilter(pattern=("users", WILDCARD))
        filters = {f1, f2, f3}
        assert len(filters) == 2

    def test_wildcard_filter_as_dict_key(self) -> None:
        """Test wildcard filter can be used as dict key."""
        f1 = WildcardFilter(pattern=("users", WILDCARD))
        f2 = WildcardFilter(pattern=("users", WILDCARD))
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# LengthFilter Tests
# =============================================================================


class TestLengthFilter:
    """Tests for LengthFilter."""

    def test_matches_exact_length_zero(self) -> None:
        """Test matching key with exact length 0."""
        f = LengthFilter(length=0)
        assert f.matches(())
        assert not f.matches(("a",))

    def test_matches_exact_length_one(self) -> None:
        """Test matching key with exact length 1."""
        f = LengthFilter(length=1)
        assert f.matches(("a",))
        assert f.matches(("users",))
        assert not f.matches(())
        assert not f.matches(("a", "b"))

    def test_matches_exact_length_three(self) -> None:
        """Test matching key with exact length 3."""
        f = LengthFilter(length=3)
        assert f.matches(("a", "b", "c"))
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("a", "b"))
        assert not f.matches(("a", "b", "c", "d"))

    def test_no_match_too_short(self) -> None:
        """Test key shorter than target length does not match."""
        f = LengthFilter(length=5)
        assert not f.matches(())
        assert not f.matches(("a",))
        assert not f.matches(("a", "b", "c", "d"))

    def test_no_match_too_long(self) -> None:
        """Test key longer than target length does not match."""
        f = LengthFilter(length=2)
        assert not f.matches(("a", "b", "c"))
        assert not f.matches(("a", "b", "c", "d"))

    def test_integer_segments(self) -> None:
        """Test matching with integer segments."""
        f = LengthFilter(length=2)
        assert f.matches((1, 2))
        assert f.matches(("a", 1))
        assert not f.matches((1,))
        assert not f.matches((1, 2, 3))

    def test_length_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same length."""
        f1 = LengthFilter(length=3)
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_length_filter_equality_same_length(self) -> None:
        """Test equality for filters with same length."""
        f1 = LengthFilter(length=3)
        f2 = LengthFilter(length=3)
        assert f1 == f2

    def test_length_filter_inequality_different_length(self) -> None:
        """Test inequality for filters with different lengths."""
        f1 = LengthFilter(length=3)
        f2 = LengthFilter(length=5)
        assert f1 != f2

    def test_length_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = LengthFilter(length=3)
        assert f != 3
        assert f.__eq__(None) == NotImplemented

    def test_length_filter_in_set(self) -> None:
        """Test length filter can be used in sets."""
        f1 = LengthFilter(length=2)
        f2 = LengthFilter(length=3)
        f3 = LengthFilter(length=2)
        filters = {f1, f2, f3}
        assert len(filters) == 2

    def test_length_filter_as_dict_key(self) -> None:
        """Test length filter can be used as dict key."""
        f1 = LengthFilter(length=3)
        f2 = LengthFilter(length=3)
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# And Filter Tests
# =============================================================================


class TestAndFilter:
    """Tests for And filter."""

    def test_matches_all_filters_true(self) -> None:
        """Test matching when all filters match."""
        f = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert f.matches(("users", "alice", "profile"))

    def test_no_match_first_filter_fails(self) -> None:
        """Test non-matching when first filter fails."""
        f = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("posts", "123", "title"))

    def test_no_match_second_filter_fails(self) -> None:
        """Test non-matching when second filter fails."""
        f = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("users", "alice"))

    def test_no_match_multiple_filters_fail(self) -> None:
        """Test non-matching when multiple filters fail."""
        f = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("posts", "bob"))

    def test_three_filters_all_match(self) -> None:
        """Test with three filters all matching."""
        f = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                SuffixFilter(suffix=("profile",)),
                LengthFilter(length=3),
            )
        )
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("users", "alice", "settings"))
        assert not f.matches(("posts", "bob", "profile"))

    def test_empty_filters_matches_all(self) -> None:
        """Test empty filters tuple matches all keys."""
        f = And(filters=())
        assert f.matches(())
        assert f.matches(("a",))
        assert f.matches(("a", "b", "c"))

    def test_single_filter_in_and(self) -> None:
        """Test And with single filter."""
        f = And(filters=(PrefixFilter(prefix=("users",)),))
        assert f.matches(("users", "alice"))
        assert not f.matches(("posts",))

    def test_wildcard_in_and(self) -> None:
        """Test And with wildcard filter."""
        f = And(
            filters=(
                WildcardFilter(pattern=("users", WILDCARD, "profile")),
                LengthFilter(length=3),
            )
        )
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("users", "bob", "profile"))
        assert not f.matches(("users", "alice", "settings"))
        assert not f.matches(("users", "alice", "profile", "extra"))

    def test_and_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same filters."""
        f1 = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_and_filter_equality_same_filters(self) -> None:
        """Test equality for And with same filters."""
        f1 = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        f2 = And(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert f1 == f2

    def test_and_filter_inequality_different_filters(self) -> None:
        """Test inequality for And with different filters."""
        f1 = And(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3)))
        f2 = And(filters=(PrefixFilter(prefix=("posts",)), LengthFilter(length=3)))
        assert f1 != f2

    def test_and_filter_inequality_different_order(self) -> None:
        """Test inequality when filter order differs."""
        pf = PrefixFilter(prefix=("users",))
        lf = LengthFilter(length=3)
        f1 = And(filters=(pf, lf))
        f2 = And(filters=(lf, pf))
        assert f1 != f2

    def test_and_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = And(filters=(PrefixFilter(prefix=("users",)),))
        assert f != (PrefixFilter(prefix=("users",)),)
        assert f.__eq__(None) == NotImplemented

    def test_and_filter_in_set(self) -> None:
        """Test And filter can be used in sets."""
        f1 = And(filters=(PrefixFilter(prefix=("users",)),))
        f2 = And(filters=(PrefixFilter(prefix=("posts",)),))
        f3 = And(filters=(PrefixFilter(prefix=("users",)),))
        filters = {f1, f2, f3}
        assert len(filters) == 2

    def test_and_filter_as_dict_key(self) -> None:
        """Test And filter can be used as dict key."""
        f1 = And(filters=(PrefixFilter(prefix=("users",)),))
        f2 = And(filters=(PrefixFilter(prefix=("users",)),))
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# Or Filter Tests
# =============================================================================


class TestOrFilter:
    """Tests for Or filter."""

    def test_matches_when_first_filter_matches(self) -> None:
        """Test matching when first filter matches."""
        f = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        assert f.matches(("users", "alice"))

    def test_matches_when_second_filter_matches(self) -> None:
        """Test matching when second filter matches."""
        f = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        assert f.matches(("posts", "123"))

    def test_matches_when_both_filters_match(self) -> None:
        """Test matching when both filters match."""
        f = Or(
            filters=(
                PrefixFilter(prefix=("data",)),
                LengthFilter(length=2),
            )
        )
        assert f.matches(("data", "value"))

    def test_no_match_when_no_filters_match(self) -> None:
        """Test non-matching when no filters match."""
        f = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        assert not f.matches(("comments", "1"))

    def test_empty_filters_matches_none(self) -> None:
        """Test empty Or filters matches nothing."""
        f = Or(filters=())
        assert not f.matches(())
        assert not f.matches(("a",))
        assert not f.matches(("a", "b", "c"))

    def test_single_filter_in_or(self) -> None:
        """Test Or with single filter."""
        f = Or(filters=(PrefixFilter(prefix=("users",)),))
        assert f.matches(("users", "alice"))
        assert not f.matches(("posts",))

    def test_three_filters_one_matches(self) -> None:
        """Test with three filters where one matches."""
        f = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
                PrefixFilter(prefix=("comments",)),
            )
        )
        assert f.matches(("comments", "123"))
        assert not f.matches(("admin",))

    def test_or_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same filters."""
        f1 = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_or_filter_equality_same_filters(self) -> None:
        """Test equality for Or with same filters."""
        f1 = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        f2 = Or(
            filters=(
                PrefixFilter(prefix=("users",)),
                PrefixFilter(prefix=("posts",)),
            )
        )
        assert f1 == f2

    def test_or_filter_inequality_different_filters(self) -> None:
        """Test inequality for Or with different filters."""
        f1 = Or(filters=(PrefixFilter(prefix=("users",)),))
        f2 = Or(filters=(PrefixFilter(prefix=("posts",)),))
        assert f1 != f2

    def test_or_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = Or(filters=(PrefixFilter(prefix=("users",)),))
        assert f != (PrefixFilter(prefix=("users",)),)
        assert f.__eq__(None) == NotImplemented


# =============================================================================
# PassAll and PassNone Tests
# =============================================================================


class TestPassAll:
    """Tests for PassAll filter."""

    def test_matches_empty_key(self) -> None:
        """Test PassAll matches empty key."""
        f = PassAll()
        assert f.matches(())

    def test_matches_any_key(self) -> None:
        """Test PassAll matches any key."""
        f = PassAll()
        assert f.matches(("users",))
        assert f.matches(("users", "alice", "profile"))
        assert f.matches((1, 2, 3, 4, 5))

    def test_passall_hash_consistent(self) -> None:
        """Test hash is consistent."""
        f1 = PassAll()
        f2 = PassAll()
        assert hash(f1) == hash(f2)

    def test_passall_equality(self) -> None:
        """Test equality."""
        f1 = PassAll()
        f2 = PassAll()
        assert f1 == f2

    def test_passall_not_equal_to_other_types(self) -> None:
        """Test not equal to other types."""
        f = PassAll()
        assert f != True
        assert f.__eq__(None) == NotImplemented


class TestPassNone:
    """Tests for PassNone filter."""

    def test_no_match_empty_key(self) -> None:
        """Test PassNone does not match empty key."""
        f = PassNone()
        assert not f.matches(())

    def test_no_match_any_key(self) -> None:
        """Test PassNone does not match any key."""
        f = PassNone()
        assert not f.matches(("users",))
        assert not f.matches(("users", "alice", "profile"))
        assert not f.matches((1, 2, 3, 4, 5))

    def test_passnone_hash_consistent(self) -> None:
        """Test hash is consistent."""
        f1 = PassNone()
        f2 = PassNone()
        assert hash(f1) == hash(f2)

    def test_passnone_equality(self) -> None:
        """Test equality."""
        f1 = PassNone()
        f2 = PassNone()
        assert f1 == f2

    def test_passnone_not_equal_to_other_types(self) -> None:
        """Test not equal to other types."""
        f = PassNone()
        assert f != False
        assert f.__eq__(None) == NotImplemented


# =============================================================================
# Operator Composition Tests
# =============================================================================


class TestOperatorComposition:
    """Tests for & and | operator composition."""

    def test_and_operator_creates_and_filter(self) -> None:
        """Test & operator creates And filter."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = LengthFilter(length=3)
        composed = f1 & f2
        assert isinstance(composed, And)
        assert composed.filters == (f1, f2)

    def test_or_operator_creates_or_filter(self) -> None:
        """Test | operator creates Or filter."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        composed = f1 | f2
        assert isinstance(composed, Or)
        assert composed.filters == (f1, f2)

    def test_and_operator_matches_correctly(self) -> None:
        """Test & operator result matches correctly."""
        composed = PrefixFilter(prefix=("users",)) & LengthFilter(length=3)
        assert composed.matches(("users", "alice", "profile"))
        assert not composed.matches(("users", "alice"))
        assert not composed.matches(("posts", "123", "title"))

    def test_or_operator_matches_correctly(self) -> None:
        """Test | operator result matches correctly."""
        composed = PrefixFilter(prefix=("users",)) | PrefixFilter(prefix=("posts",))
        assert composed.matches(("users", "alice"))
        assert composed.matches(("posts", "123"))
        assert not composed.matches(("comments",))

    def test_chained_and_operators(self) -> None:
        """Test chaining multiple & operators."""
        composed = (
            PrefixFilter(prefix=("users",))
            & LengthFilter(length=3)
            & SuffixFilter(suffix=("profile",))
        )
        assert composed.matches(("users", "alice", "profile"))
        assert not composed.matches(("users", "alice", "settings"))

    def test_chained_or_operators(self) -> None:
        """Test chaining multiple | operators."""
        composed = (
            PrefixFilter(prefix=("users",))
            | PrefixFilter(prefix=("posts",))
            | PrefixFilter(prefix=("comments",))
        )
        assert composed.matches(("users",))
        assert composed.matches(("posts",))
        assert composed.matches(("comments",))
        assert not composed.matches(("admin",))

    def test_mixed_and_or_operators(self) -> None:
        """Test mixing & and | operators."""
        # (users prefix AND length 2) OR (posts prefix)
        composed = (PrefixFilter(prefix=("users",)) & LengthFilter(length=2)) | PrefixFilter(
            prefix=("posts",)
        )
        assert composed.matches(("users", "alice"))
        assert composed.matches(("posts", "123", "title"))
        assert not composed.matches(("users", "alice", "profile"))
        assert not composed.matches(("comments",))


# =============================================================================
# Flattening Tests
# =============================================================================


class TestAndFlattening:
    """Tests for And filter flattening."""

    def test_and_with_and_flattens(self) -> None:
        """Test And & And flattens to single And."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = LengthFilter(length=3)
        f3 = SuffixFilter(suffix=("profile",))

        and1 = And(filters=(f1, f2))
        result = and1 & f3

        assert isinstance(result, And)
        assert result.filters == (f1, f2, f3)

    def test_nested_and_flattening(self) -> None:
        """Test nested And flattening."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = LengthFilter(length=3)
        f3 = SuffixFilter(suffix=("profile",))
        f4 = WildcardFilter(pattern=("users", WILDCARD, "profile"))

        and1 = And(filters=(f1, f2))
        and2 = And(filters=(f3, f4))
        result = and1 & and2

        assert isinstance(result, And)
        assert result.filters == (f1, f2, f3, f4)

    def test_chained_and_operator_flattening(self) -> None:
        """Test chained & operators flatten."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = LengthFilter(length=3)
        f3 = SuffixFilter(suffix=("profile",))

        result = f1 & f2 & f3

        assert isinstance(result, And)
        assert len(result.filters) == 3
        assert result.filters == (f1, f2, f3)


class TestOrFlattening:
    """Tests for Or filter flattening."""

    def test_or_with_or_flattens(self) -> None:
        """Test Or | Or flattens to single Or."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        f3 = PrefixFilter(prefix=("comments",))

        or1 = Or(filters=(f1, f2))
        result = or1 | f3

        assert isinstance(result, Or)
        assert result.filters == (f1, f2, f3)

    def test_nested_or_flattening(self) -> None:
        """Test nested Or flattening."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        f3 = PrefixFilter(prefix=("comments",))
        f4 = PrefixFilter(prefix=("admin",))

        or1 = Or(filters=(f1, f2))
        or2 = Or(filters=(f3, f4))
        result = or1 | or2

        assert isinstance(result, Or)
        assert result.filters == (f1, f2, f3, f4)

    def test_chained_or_operator_flattening(self) -> None:
        """Test chained | operators flatten."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        f3 = PrefixFilter(prefix=("comments",))

        result = f1 | f2 | f3

        assert isinstance(result, Or)
        assert len(result.filters) == 3
        assert result.filters == (f1, f2, f3)


# =============================================================================
# Cross-Filter Type Tests
# =============================================================================


class TestCrossFilterComparisons:
    """Tests for comparing different filter types."""

    def test_different_filter_types_not_equal(self) -> None:
        """Test filters of different types are not equal."""
        pf = PrefixFilter(prefix=("users",))
        sf = SuffixFilter(suffix=("users",))
        assert pf != sf

    def test_prefix_and_suffix_different_objects(self) -> None:
        """Test prefix and suffix filters are different objects."""
        pf = PrefixFilter(prefix=("users",))
        sf = SuffixFilter(suffix=("users",))
        assert hash(pf) != hash(sf)

    def test_filters_in_mixed_set(self) -> None:
        """Test different filter types can be in same set."""
        pf = PrefixFilter(prefix=("users",))
        sf = SuffixFilter(suffix=("users",))
        lf = LengthFilter(length=1)
        wf = WildcardFilter(pattern=("users",))
        filters = {pf, sf, lf, wf}
        assert len(filters) == 4

    def test_filters_in_mixed_dict(self) -> None:
        """Test different filter types can be dict keys."""
        pf = PrefixFilter(prefix=("users",))
        sf = SuffixFilter(suffix=("users",))
        d = {pf: "prefix", sf: "suffix"}
        assert d[pf] == "prefix"
        assert d[sf] == "suffix"


# =============================================================================
# Wildcard Constant Tests
# =============================================================================


class TestWildcardConstant:
    """Tests for the WILDCARD constant."""

    def test_wildcard_is_string_asterisk(self) -> None:
        """Test WILDCARD constant is the string '*'."""
        assert WILDCARD == "*"

    def test_wildcard_can_be_used_in_pattern(self) -> None:
        """Test WILDCARD can be used in patterns."""
        f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        assert f.matches(("users", "alice", "profile"))

    def test_wildcard_string_literal_matches(self) -> None:
        """Test using string literal '*' in pattern."""
        f = WildcardFilter(pattern=("users", "*", "profile"))
        assert f.matches(("users", "alice", "profile"))


# =============================================================================
# Filter ABC Tests
# =============================================================================


class TestFilterABC:
    """Tests for Filter abstract base class."""

    def test_filter_is_abstract(self) -> None:
        """Test Filter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Filter()  # type: ignore

    def test_all_concrete_filters_inherit_from_filter(self) -> None:
        """Test all concrete filters inherit from Filter."""
        assert issubclass(PrefixFilter, Filter)
        assert issubclass(SuffixFilter, Filter)
        assert issubclass(LengthFilter, Filter)
        assert issubclass(WildcardFilter, Filter)
        assert issubclass(And, Filter)
        assert issubclass(Or, Filter)
        assert issubclass(PassAll, Filter)
        assert issubclass(PassNone, Filter)
