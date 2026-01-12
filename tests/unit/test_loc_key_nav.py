"""Unit tests for the key_nav module - key construction and flat operations.

This test module covers key manipulation functions that are flat (non-hierarchical):
- Key construction with DATA_ROOT
- Metadata key conversion
- Key joining and depth operations

For hierarchical operations (ancestors, descendants), see test_loc_site_nav.py.
"""

from everyshape.loc import (
    DATA_ROOT,
    METADATA_ROOT,
)
from everyshape.loc.key import (
    create_key,
    get_depth,
    join_key,
    join_segment,
    to_meta,
)


class TestConstants:
    """Tests for module constants."""

    def test_data_root_constant(self) -> None:
        """Test DATA_ROOT constant has expected value."""
        assert DATA_ROOT == "/"

    def test_metadata_root_constant(self) -> None:
        """Test METADATA_ROOT constant has expected value."""
        assert METADATA_ROOT == "/m"


class TestCreateKey:
    """Tests for create_key function."""

    def test_create_key_single_segment(self) -> None:
        """Test creating key with single segment."""
        key = create_key("users")
        assert key == (DATA_ROOT, "users")

    def test_create_key_multiple_segments(self) -> None:
        """Test creating key with multiple segments."""
        key = create_key("users", "alice")
        assert key == (DATA_ROOT, "users", "alice")

    def test_create_key_three_segments(self) -> None:
        """Test creating key with three segments."""
        key = create_key("users", "alice", "profile")
        assert key == (DATA_ROOT, "users", "alice", "profile")

    def test_create_key_no_segments(self) -> None:
        """Test creating key with no segments returns just root."""
        key = create_key()
        assert key == (DATA_ROOT,)

    def test_create_key_with_integer_segment(self) -> None:
        """Test creating key with integer segment."""
        key = create_key("items", 1)
        assert key == (DATA_ROOT, "items", 1)

    def test_create_key_with_mixed_segments(self) -> None:
        """Test creating key with mixed string and integer segments."""
        key = create_key("users", "alice", 42, "posts")
        assert key == (DATA_ROOT, "users", "alice", 42, "posts")

    def test_create_key_includes_data_root_prefix(self) -> None:
        """Test that created keys always have DATA_ROOT prefix."""
        key = create_key("a", "b", "c")
        assert key[0] == DATA_ROOT


class TestToMeta:
    """Tests for to_meta function."""

    def test_to_meta_basic(self) -> None:
        """Test converting key to metadata version."""
        key = create_key("users", "alice")
        meta_key = to_meta(key)
        assert meta_key == (METADATA_ROOT, "users", "alice")

    def test_to_meta_replaces_root_only(self) -> None:
        """Test that to_meta only replaces the root marker."""
        key = (DATA_ROOT, "a", "b", "c")
        meta_key = to_meta(key)
        assert meta_key[0] == METADATA_ROOT
        assert meta_key[1:] == key[1:]

    def test_to_meta_single_segment(self) -> None:
        """Test converting single-segment key to metadata."""
        key = (DATA_ROOT, "users")
        meta_key = to_meta(key)
        assert meta_key == (METADATA_ROOT, "users")

    def test_to_meta_preserves_segments(self) -> None:
        """Test that to_meta preserves all segments after root."""
        key = (DATA_ROOT, "x", "y", "z", 1, 2)
        meta_key = to_meta(key)
        assert meta_key[1:] == ("x", "y", "z", 1, 2)

    def test_to_meta_from_created_key(self) -> None:
        """Test to_meta on a key created with create_key."""
        key = create_key("items", 42)
        meta_key = to_meta(key)
        assert meta_key == (METADATA_ROOT, "items", 42)

    def test_to_meta_roundtrip_behavior(self) -> None:
        """Test that to_meta can be applied again to any key."""
        key = create_key("users", "bob")
        meta_key = to_meta(key)
        meta_again = to_meta(meta_key)
        # Second application should still produce metadata root
        assert meta_again[0] == METADATA_ROOT


class TestGetDepth:
    """Tests for get_depth function."""

    def test_get_depth_empty_key(self) -> None:
        """Test depth of empty key is 0."""
        assert get_depth(()) == 0

    def test_get_depth_single_segment(self) -> None:
        """Test depth of single-segment key is 1."""
        assert get_depth(("users",)) == 1

    def test_get_depth_two_segments(self) -> None:
        """Test depth of two-segment key is 2."""
        assert get_depth(("users", "alice")) == 2

    def test_get_depth_multiple_segments(self) -> None:
        """Test depth equals number of segments."""
        key = ("a", "b", "c", "d", "e")
        assert get_depth(key) == 5

    def test_get_depth_with_data_root(self) -> None:
        """Test depth includes DATA_ROOT marker."""
        key = (DATA_ROOT, "users", "alice")
        assert get_depth(key) == 3

    def test_get_depth_with_integer_segments(self) -> None:
        """Test depth with integer segments."""
        key = ("items", 1, "details", 2)
        assert get_depth(key) == 4


class TestJoinKey:
    """Tests for join_key function."""

    def test_join_key_string_segments(self) -> None:
        """Test joining simple string segments."""
        result = join_key("users", "alice")
        assert result == ("users", "alice")

    def test_join_key_single_segment(self) -> None:
        """Test joining single segment."""
        result = join_key("users")
        assert result == ("users",)

    def test_join_key_multiple_segments(self) -> None:
        """Test joining multiple segments."""
        result = join_key("a", "b", "c", "d")
        assert result == ("a", "b", "c", "d")

    def test_join_key_tuple_segments(self) -> None:
        """Test joining with tuple keys."""
        result = join_key(("users",), "alice")
        assert result == ("users", "alice")

    def test_join_key_multiple_tuples(self) -> None:
        """Test joining multiple tuple keys."""
        result = join_key(("users",), ("alice", "posts"), ("1",))
        assert result == ("users", "alice", "posts", "1")

    def test_join_key_mixed_segments_and_tuples(self) -> None:
        """Test joining mixed segments and tuples."""
        result = join_key("users", ("alice",), "posts", ("1",))
        assert result == ("users", "alice", "posts", "1")

    def test_join_key_empty_tuple(self) -> None:
        """Test joining with empty tuple."""
        result = join_key("users", (), "alice")
        assert result == ("users", "alice")

    def test_join_key_integer_segments(self) -> None:
        """Test joining with integer segments."""
        result = join_key("items", 1, "details", 2)
        assert result == ("items", 1, "details", 2)

    def test_join_key_no_arguments(self) -> None:
        """Test joining with no arguments."""
        result = join_key()
        assert result == ()

    def test_join_key_flattens_nested_tuples(self) -> None:
        """Test that join_key properly flattens tuple arguments."""
        result = join_key(("a", "b", "c"), ("d", "e"))
        assert result == ("a", "b", "c", "d", "e")
        assert isinstance(result, tuple)


class TestJoinSegment:
    """Tests for join_segment function."""

    def test_join_segment_basic(self) -> None:
        """Test appending segment to key."""
        key = ("users",)
        result = join_segment(key, "alice")
        assert result == ("users", "alice")

    def test_join_segment_multiple(self) -> None:
        """Test appending multiple segments to key."""
        key = ("users",)
        result = join_segment(key, "alice", "posts")
        assert result == ("users", "alice", "posts")

    def test_join_segment_to_empty_key(self) -> None:
        """Test appending segment to empty key."""
        key = ()
        result = join_segment(key, "users")
        assert result == ("users",)

    def test_join_segment_deep_key(self) -> None:
        """Test appending segment to deeply nested key."""
        key = ("a", "b", "c")
        result = join_segment(key, "d", "e")
        assert result == ("a", "b", "c", "d", "e")

    def test_join_segment_with_data_root(self) -> None:
        """Test appending segment to key with DATA_ROOT."""
        key = (DATA_ROOT, "users")
        result = join_segment(key, "alice")
        assert result == (DATA_ROOT, "users", "alice")

    def test_join_segment_integer_segments(self) -> None:
        """Test appending integer segments."""
        key = ("items",)
        result = join_segment(key, 1, 2, 3)
        assert result == ("items", 1, 2, 3)

    def test_join_segment_mixed_segments(self) -> None:
        """Test appending mixed segment types."""
        key = ("users", "alice")
        result = join_segment(key, "posts", 1, "comments")
        assert result == ("users", "alice", "posts", 1, "comments")


class TestIntegrationScenarios:
    """Integration tests combining multiple functions."""

    def test_scenario_metadata_tracking(self) -> None:
        """Test metadata key creation and conversion."""
        data_key = create_key("users", "alice")
        meta_key = to_meta(data_key)

        # Both should have same segments except root
        assert data_key[1:] == meta_key[1:]
        assert data_key[0] == DATA_ROOT
        assert meta_key[0] == METADATA_ROOT

    def test_scenario_key_construction(self) -> None:
        """Test building keys from components."""
        base = ("users",)
        user_id = "alice"
        sub_path = ("posts", 1)

        # Combine using different methods
        key1 = join_segment(base, user_id, *sub_path)
        key2 = join_key(base, user_id, sub_path)

        assert key1 == ("users", "alice", "posts", 1)
        assert key2 == ("users", "alice", "posts", 1)
