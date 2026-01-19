"""Unit tests for path helper functions in loc/path_nav.py.

Tests the core path manipulation functions without requiring View objects:
- build_view_path: builds PathToView from segments
- build_value_path: builds PathToValue from segments
- split_value_path: splits PathToValue into parent and value segment
- split_path: splits path at index
- parent_view_path: removes last segment
- last_segment: gets last segment
"""

from everykv.loc.path import (
    build_value_path,
    build_view_path,
    last_segment,
    parent_view_path,
    split_path,
    split_value_path,
)


# =============================================================================
# TEST DATA SETUP
# =============================================================================


# We use simple type objects instead of actual View classes
class MockDictView:
    """Mock View type for testing."""

    pass


class MockListView:
    """Mock View type for testing."""

    pass


# Helper to create PathViewSegment tuples (address, ViewType)
def path_segment(address, view_type):
    """Create a path view segment."""
    return (address, view_type)


# Helper to create PathValueSegment tuples (address, ValueType)
def value_segment(address, value_type):
    """Create a path value segment."""
    return (address, value_type)


# =============================================================================
# TEST build_view_path
# =============================================================================


class TestBuildViewPath:
    """Tests for build_view_path(*segments) -> PathToView."""

    def test_empty_path(self):
        """Build empty view path."""
        path = build_view_path()
        assert path == ()
        assert isinstance(path, tuple)

    def test_single_segment(self):
        """Build view path with single segment."""
        path = build_view_path(("users", MockDictView))
        assert path == (("users", MockDictView),)
        assert len(path) == 1

    def test_multiple_segments(self):
        """Build view path with multiple segments."""
        path = build_view_path(
            ("users", MockDictView),
            ("alice", MockDictView),
        )
        assert path == (("users", MockDictView), ("alice", MockDictView))
        assert len(path) == 2

    def test_nested_path_three_segments(self):
        """Build deeply nested view path."""
        path = build_view_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
        )
        assert path == (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
        )
        assert len(path) == 3

    def test_integer_address_segment(self):
        """Build view path with integer address (like list index)."""
        path = build_view_path(
            ("items", MockListView),
            (0, MockDictView),
        )
        assert path == (("items", MockListView), (0, MockDictView))

    def test_negative_index_segment(self):
        """Build view path with negative index."""
        path = build_view_path(
            ("items", MockListView),
            (-1, MockDictView),
        )
        assert path == (("items", MockListView), (-1, MockDictView))

    def test_docstring_example(self):
        """Test example from docstring."""
        path = build_view_path(
            ("users", MockDictView),
            ("alice", MockDictView),
        )
        assert path == (("users", MockDictView), ("alice", MockDictView))


# =============================================================================
# TEST build_value_path
# =============================================================================


class TestBuildValuePath:
    """Tests for build_value_path(*segments, v=value_segment) -> PathToValue."""

    def test_value_segment_only(self):
        """Build value path with only value segment."""
        path = build_value_path(v=("name", str))
        assert path == (("name", str),)
        assert len(path) == 1

    def test_single_view_segment_and_value(self):
        """Build value path with one view segment and value segment."""
        path = build_value_path(
            ("users", MockDictView),
            v=("count", int),
        )
        assert path == (("users", MockDictView), ("count", int))
        assert len(path) == 2

    def test_multiple_view_segments_and_value(self):
        """Build value path with multiple view segments and value segment."""
        path = build_value_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            v=("name", str),
        )
        assert path == (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("name", str),
        )
        assert len(path) == 3

    def test_nested_value_path(self):
        """Build deeply nested value path."""
        path = build_value_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
            v=(-1, str),
        )
        assert path == (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
            (-1, str),
        )
        assert len(path) == 4

    def test_various_value_types(self):
        """Build value paths with various value types."""
        path_str = build_value_path(("data", MockDictView), v=("key", str))
        path_int = build_value_path(("data", MockDictView), v=("count", int))
        path_float = build_value_path(("data", MockDictView), v=("price", float))
        path_list = build_value_path(("data", MockDictView), v=("items", list))
        path_dict = build_value_path(("data", MockDictView), v=("meta", dict))

        assert path_str[-1] == ("key", str)
        assert path_int[-1] == ("count", int)
        assert path_float[-1] == ("price", float)
        assert path_list[-1] == ("items", list)
        assert path_dict[-1] == ("meta", dict)

    def test_docstring_example(self):
        """Test example from docstring."""
        path = build_value_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            v=("name", str),
        )
        assert path == (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("name", str),
        )


# =============================================================================
# TEST split_value_path
# =============================================================================


class TestSplitValuePath:
    """Tests for split_value_path(path) -> (PathToView, PathValueSegment)."""

    def test_single_value_segment(self):
        """Split path with only value segment."""
        path = (("name", str),)
        parent, value_seg = split_value_path(path)
        assert parent == ()
        assert value_seg == ("name", str)

    def test_two_segment_path(self):
        """Split path with one view segment and one value segment."""
        path = (("users", MockDictView), ("count", int))
        parent, value_seg = split_value_path(path)
        assert parent == (("users", MockDictView),)
        assert value_seg == ("count", int)

    def test_three_segment_path(self):
        """Split path with two view segments and one value segment."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        parent, value_seg = split_value_path(path)
        assert parent == (("users", MockDictView), ("alice", MockDictView))
        assert value_seg == ("name", str)

    def test_docstring_example(self):
        """Test example from docstring."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        parent, (address, type_) = split_value_path(path)
        assert parent == (("users", MockDictView), ("alice", MockDictView))
        assert address == "name"
        assert type_ is str

    def test_negative_index_value_segment(self):
        """Split path where value segment has negative index."""
        path = (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
            (-1, str),
        )
        parent, value_seg = split_value_path(path)
        assert parent == (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
        )
        assert value_seg == (-1, str)

    def test_preserves_path_structure(self):
        """Verify that split preserves the full path when reassembled."""
        original_path = (("a", MockDictView), ("b", MockDictView), ("c", str))
        parent, value_seg = split_value_path(original_path)
        reassembled = (*parent, value_seg)
        assert reassembled == original_path


# =============================================================================
# TEST split_path
# =============================================================================


class TestSplitPath:
    """Tests for split_path(path, index) -> (Path, Path)."""

    def test_split_at_zero(self):
        """Split path at index 0."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        left, right = split_path(path, 0)
        assert left == ()
        assert right == (("users", MockDictView), ("alice", MockDictView), ("name", str))

    def test_split_at_one(self):
        """Split path at index 1."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        left, right = split_path(path, 1)
        assert left == (("users", MockDictView),)
        assert right == (("alice", MockDictView), ("name", str))

    def test_split_at_two(self):
        """Split path at index 2."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        left, right = split_path(path, 2)
        assert left == (("users", MockDictView), ("alice", MockDictView))
        assert right == (("name", str),)

    def test_split_at_end(self):
        """Split path at the end (full length)."""
        path = (("users", MockDictView), ("alice", MockDictView))
        left, right = split_path(path, len(path))
        assert left == (("users", MockDictView), ("alice", MockDictView))
        assert right == ()

    def test_empty_path_split(self):
        """Split empty path."""
        path = ()
        left, right = split_path(path, 0)
        assert left == ()
        assert right == ()

    def test_single_segment_split_at_zero(self):
        """Split single segment path at 0."""
        path = (("users", MockDictView),)
        left, right = split_path(path, 0)
        assert left == ()
        assert right == (("users", MockDictView),)

    def test_single_segment_split_at_one(self):
        """Split single segment path at 1."""
        path = (("users", MockDictView),)
        left, right = split_path(path, 1)
        assert left == (("users", MockDictView),)
        assert right == ()

    def test_reassembly_preserves_path(self):
        """Verify that split and reassemble preserves original path."""
        original_path = (("a", MockDictView), ("b", MockDictView), ("c", str))
        for index in range(len(original_path) + 1):
            left, right = split_path(original_path, index)
            reassembled = (*left, *right)
            assert reassembled == original_path


# =============================================================================
# TEST parent_view_path
# =============================================================================


class TestParentViewPath:
    """Tests for parent_view_path(path) -> PathToView."""

    def test_single_segment_path(self):
        """Get parent of single segment path returns empty path."""
        path = (("users", MockDictView),)
        parent = parent_view_path(path)
        assert parent == ()

    def test_two_segment_path(self):
        """Get parent of two segment path."""
        path = (("users", MockDictView), ("alice", MockDictView))
        parent = parent_view_path(path)
        assert parent == (("users", MockDictView),)

    def test_three_segment_path(self):
        """Get parent of three segment path."""
        path = (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
        )
        parent = parent_view_path(path)
        assert parent == (
            ("users", MockDictView),
            ("alice", MockDictView),
        )

    def test_value_path_parent(self):
        """Get parent of value path (returns all view segments)."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        parent = parent_view_path(path)
        assert parent == (("users", MockDictView), ("alice", MockDictView))

    def test_docstring_example(self):
        """Test example from docstring."""
        path = (("users", MockDictView), ("alice", MockDictView))
        parent = parent_view_path(path)
        assert parent == (("users", MockDictView),)

    def test_deeply_nested_path(self):
        """Get parent of deeply nested path."""
        path = (
            ("a", MockDictView),
            ("b", MockListView),
            ("c", MockDictView),
            ("d", MockDictView),
        )
        parent = parent_view_path(path)
        assert parent == (
            ("a", MockDictView),
            ("b", MockListView),
            ("c", MockDictView),
        )


# =============================================================================
# TEST last_segment
# =============================================================================


class TestLastSegment:
    """Tests for last_segment(path) -> PathSegment."""

    def test_single_segment_path(self):
        """Get last segment of single segment path."""
        path = (("users", MockDictView),)
        last = last_segment(path)
        assert last == ("users", MockDictView)

    def test_two_segment_path(self):
        """Get last segment of two segment path."""
        path = (("users", MockDictView), ("alice", MockDictView))
        last = last_segment(path)
        assert last == ("alice", MockDictView)

    def test_three_segment_path(self):
        """Get last segment of three segment path."""
        path = (
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
        )
        last = last_segment(path)
        assert last == ("tags", MockListView)

    def test_value_path_last_segment(self):
        """Get last segment of value path (returns value segment)."""
        path = (("users", MockDictView), ("alice", MockDictView), ("name", str))
        last = last_segment(path)
        assert last == ("name", str)

    def test_docstring_example(self):
        """Test example from docstring."""
        path = (("users", MockDictView), ("alice", MockDictView))
        last = last_segment(path)
        assert last == ("alice", MockDictView)

    def test_integer_address_last_segment(self):
        """Get last segment with integer address."""
        path = (("items", MockListView), (0, MockDictView))
        last = last_segment(path)
        assert last == (0, MockDictView)

    def test_negative_index_last_segment(self):
        """Get last segment with negative index."""
        path = (("items", MockListView), (-1, str))
        last = last_segment(path)
        assert last == (-1, str)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestPathFunctionsIntegration:
    """Integration tests for path functions working together."""

    def test_build_and_split_value_path(self):
        """Build value path and split it back."""
        original_path = build_value_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            v=("name", str),
        )
        parent, value_seg = split_value_path(original_path)
        reassembled = (*parent, value_seg)
        assert reassembled == original_path

    def test_build_and_get_last_segment(self):
        """Build path and get last segment."""
        path = build_view_path(
            ("users", MockDictView),
            ("alice", MockDictView),
        )
        last = last_segment(path)
        assert last == ("alice", MockDictView)

    def test_build_and_get_parent(self):
        """Build path and get parent."""
        path = build_view_path(
            ("users", MockDictView),
            ("alice", MockDictView),
        )
        parent = parent_view_path(path)
        assert parent == (("users", MockDictView),)

    def test_complex_path_manipulation_workflow(self):
        """Test complete workflow with complex path."""
        # Build a complex path
        path = build_value_path(
            ("users", MockDictView),
            ("alice", MockDictView),
            ("tags", MockListView),
            v=(-1, str),
        )

        # Split to value components
        parent_view, value_seg = split_value_path(path)
        assert value_seg == (-1, str)

        # Get parent of view path
        grandparent = parent_view_path(parent_view)
        assert grandparent == (("users", MockDictView), ("alice", MockDictView))

        # Get last segment
        last = last_segment(parent_view)
        assert last == ("tags", MockListView)

    def test_path_navigation_reconstruction(self):
        """Test reconstructing path through multiple operations."""
        original = (
            ("a", MockDictView),
            ("b", MockListView),
            ("c", MockDictView),
            ("d", str),
        )

        # Split at different points
        part1, part2 = split_path(original, 1)
        part2_1, part2_2 = split_path(part2, 1)

        # Reconstruct
        reconstructed = (*part1, *part2_1, *part2_2)
        assert reconstructed == original

    def test_chained_parent_operations(self):
        """Test getting parent multiple times."""
        path = (
            ("a", MockDictView),
            ("b", MockDictView),
            ("c", MockDictView),
            ("d", str),
        )

        parent1 = parent_view_path(path)
        assert len(parent1) == 3

        parent2 = parent_view_path(parent1)
        assert len(parent2) == 2

        parent3 = parent_view_path(parent2)
        assert len(parent3) == 1

        parent4 = parent_view_path(parent3)
        assert parent4 == ()

    def test_split_and_rebuild_at_multiple_indices(self):
        """Test splitting at various indices and rebuilding."""
        path = (
            ("a", MockDictView),
            ("b", MockDictView),
            ("c", MockListView),
            ("d", MockDictView),
            ("e", str),
        )

        for i in range(len(path) + 1):
            left, right = split_path(path, i)
            rebuilt = (*left, *right)
            assert rebuilt == path
            assert len(left) + len(right) == len(path)
