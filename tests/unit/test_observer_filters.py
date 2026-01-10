"""Unit tests for subscription filters in everyshape.storage.observer.options."""

from __future__ import annotations

import pytest

from everyshape.storage.observer.options import (
    WILDCARD,
    CompositeFilter,
    LengthFilter,
    PrefixFilter,
    SubscriptionOptions,
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
        assert NotImplemented == f.__eq__(None)

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

    def test_empty_suffix_matches_only_empty_key(self) -> None:
        """Test empty suffix only matches empty key."""
        f = SuffixFilter(suffix=())
        assert f.matches(())
        # Empty suffix is only a suffix of the empty key
        assert not f.matches(("users",))

    def test_multi_segment_suffix(self) -> None:
        """Test suffix with multiple segments."""
        f = SuffixFilter(suffix=("alice", "profile"))
        assert f.matches(("alice", "profile"))
        assert f.matches(("users", "alice", "profile"))
        assert not f.matches(("users", "alice"))
        # suffix just checks if key ends with the suffix pattern, regardless of prefix
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
        assert NotImplemented == f.__eq__(None)

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
        assert NotImplemented == f.__eq__(None)

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
        assert NotImplemented == f.__eq__(None)

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
# CompositeFilter Tests
# =============================================================================


class TestCompositeFilter:
    """Tests for CompositeFilter."""

    def test_matches_all_filters_true(self) -> None:
        """Test matching when all filters match."""
        f = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert f.matches(("users", "alice", "profile"))

    def test_no_match_first_filter_fails(self) -> None:
        """Test non-matching when first filter fails."""
        f = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("posts", "123", "title"))

    def test_no_match_second_filter_fails(self) -> None:
        """Test non-matching when second filter fails."""
        f = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("users", "alice"))

    def test_no_match_multiple_filters_fail(self) -> None:
        """Test non-matching when multiple filters fail."""
        f = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert not f.matches(("posts", "bob"))

    def test_three_filters_all_match(self) -> None:
        """Test with three filters all matching."""
        f = CompositeFilter(
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
        f = CompositeFilter(filters=())
        assert f.matches(())
        assert f.matches(("a",))
        assert f.matches(("a", "b", "c"))

    def test_single_filter_in_composite(self) -> None:
        """Test composite with single filter."""
        f = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        assert f.matches(("users", "alice"))
        assert not f.matches(("posts",))

    def test_wildcard_in_composite(self) -> None:
        """Test composite with wildcard filter."""
        f = CompositeFilter(
            filters=(
                WildcardFilter(pattern=("users", WILDCARD, "profile")),
                LengthFilter(length=3),
            )
        )
        assert f.matches(("users", "alice", "profile"))
        assert f.matches(("users", "bob", "profile"))
        assert not f.matches(("users", "alice", "settings"))
        assert not f.matches(("users", "alice", "profile", "extra"))

    def test_composite_filter_hash_consistent(self) -> None:
        """Test hash is consistent for same filters."""
        f1 = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        h1 = hash(f1)
        h2 = hash(f1)
        assert h1 == h2

    def test_composite_filter_equality_same_filters(self) -> None:
        """Test equality for composites with same filters."""
        f1 = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        f2 = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        assert f1 == f2

    def test_composite_filter_inequality_different_filters(self) -> None:
        """Test inequality for composites with different filters."""
        f1 = CompositeFilter(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3)))
        f2 = CompositeFilter(filters=(PrefixFilter(prefix=("posts",)), LengthFilter(length=3)))
        assert f1 != f2

    def test_composite_filter_inequality_different_order(self) -> None:
        """Test inequality when filter order differs."""
        pf = PrefixFilter(prefix=("users",))
        lf = LengthFilter(length=3)
        f1 = CompositeFilter(filters=(pf, lf))
        f2 = CompositeFilter(filters=(lf, pf))
        assert f1 != f2

    def test_composite_filter_not_equal_to_other_types(self) -> None:
        """Test filter not equal to other types."""
        f = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        assert f != (PrefixFilter(prefix=("users",)),)
        # CompositeFilter.__eq__ returns False (not NotImplemented) for non-CompositeFilter types
        assert f != None

    def test_composite_filter_in_set(self) -> None:
        """Test composite filter can be used in sets."""
        f1 = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        f2 = CompositeFilter(filters=(PrefixFilter(prefix=("posts",)),))
        f3 = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        filters = {f1, f2, f3}
        assert len(filters) == 2

    def test_composite_filter_as_dict_key(self) -> None:
        """Test composite filter can be used as dict key."""
        f1 = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        f2 = CompositeFilter(filters=(PrefixFilter(prefix=("users",)),))
        d = {f1: "value"}
        assert d[f2] == "value"


# =============================================================================
# SubscriptionOptions Tests
# =============================================================================


class TestSubscriptionOptions:
    """Tests for SubscriptionOptions."""

    def test_initialization_with_prefix_filter(self) -> None:
        """Test initializing options with prefix filter."""
        f = PrefixFilter(prefix=("users",))
        opts = SubscriptionOptions(filter=f)
        assert opts.filter == f

    def test_initialization_with_wildcard_filter(self) -> None:
        """Test initializing options with wildcard filter."""
        f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
        opts = SubscriptionOptions(filter=f)
        assert opts.filter == f

    def test_initialization_with_composite_filter(self) -> None:
        """Test initializing options with composite filter."""
        f = CompositeFilter(
            filters=(
                PrefixFilter(prefix=("users",)),
                LengthFilter(length=3),
            )
        )
        opts = SubscriptionOptions(filter=f)
        assert opts.filter == f

    def test_options_hash_consistent(self) -> None:
        """Test hash is consistent for options."""
        f = PrefixFilter(prefix=("users",))
        opts = SubscriptionOptions(filter=f)
        h1 = hash(opts)
        h2 = hash(opts)
        assert h1 == h2

    def test_options_equality_same_filter(self) -> None:
        """Test equality for options with same filter."""
        f = PrefixFilter(prefix=("users",))
        opts1 = SubscriptionOptions(filter=f)
        opts2 = SubscriptionOptions(filter=f)
        assert opts1 == opts2

    def test_options_equality_equivalent_filters(self) -> None:
        """Test equality when filters are equivalent."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("users",))
        opts1 = SubscriptionOptions(filter=f1)
        opts2 = SubscriptionOptions(filter=f2)
        assert opts1 == opts2

    def test_options_inequality_different_filters(self) -> None:
        """Test inequality for options with different filters."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        opts1 = SubscriptionOptions(filter=f1)
        opts2 = SubscriptionOptions(filter=f2)
        assert opts1 != opts2

    def test_options_not_equal_to_other_types(self) -> None:
        """Test options not equal to other types."""
        f = PrefixFilter(prefix=("users",))
        opts = SubscriptionOptions(filter=f)
        assert opts != f
        assert opts != "options"
        assert NotImplemented == opts.__eq__(None)

    def test_options_in_set(self) -> None:
        """Test options can be used in sets."""
        f1 = PrefixFilter(prefix=("users",))
        f2 = PrefixFilter(prefix=("posts",))
        opts1 = SubscriptionOptions(filter=f1)
        opts2 = SubscriptionOptions(filter=f2)
        opts3 = SubscriptionOptions(filter=f1)
        options = {opts1, opts2, opts3}
        assert len(options) == 2

    def test_options_as_dict_key(self) -> None:
        """Test options can be used as dict key."""
        f = PrefixFilter(prefix=("users",))
        opts1 = SubscriptionOptions(filter=f)
        opts2 = SubscriptionOptions(filter=f)
        d = {opts1: "subscription"}
        assert d[opts2] == "subscription"

    def test_options_is_frozen(self) -> None:
        """Test that options cannot be modified (frozen dataclass)."""
        f = PrefixFilter(prefix=("users",))
        opts = SubscriptionOptions(filter=f)
        with pytest.raises(AttributeError):
            opts.filter = PrefixFilter(prefix=("posts",))


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
