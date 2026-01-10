"""Unit tests for the key_nav module - key traversal and navigation operations.

This test module covers all key manipulation functions with basic functionality,
edge cases, and typical use cases.
"""

from everyshape.loc.key_nav import (
    DATA_ROOT,
    METADATA_ROOT,
    create_key,
    get_ancestors,
    get_common_ancestor,
    get_depth,
    get_key_chain,
    get_parent,
    is_ancestor,
    is_descendant,
    is_sibling,
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


class TestGetParent:
    """Tests for get_parent function."""

    def test_get_parent_basic(self) -> None:
        """Test getting parent of simple key."""
        key = ("users", "alice")
        parent = get_parent(key)
        assert parent == ("users",)

    def test_get_parent_single_segment(self) -> None:
        """Test getting parent of single-segment key returns None."""
        key = ("users",)
        parent = get_parent(key)
        assert parent is None

    def test_get_parent_empty_key(self) -> None:
        """Test getting parent of empty key returns None."""
        key = ()
        parent = get_parent(key)
        assert parent is None

    def test_get_parent_deep_key(self) -> None:
        """Test getting parent of deeply nested key."""
        key = ("a", "b", "c", "d", "e")
        parent = get_parent(key)
        assert parent == ("a", "b", "c", "d")

    def test_get_parent_with_data_root(self) -> None:
        """Test getting parent of key created with DATA_ROOT."""
        key = (DATA_ROOT, "users", "alice")
        parent = get_parent(key)
        assert parent == (DATA_ROOT, "users")

    def test_get_parent_of_data_root_only(self) -> None:
        """Test getting parent of DATA_ROOT only returns None."""
        key = (DATA_ROOT,)
        parent = get_parent(key)
        assert parent is None


class TestGetAncestors:
    """Tests for get_ancestors function."""

    def test_get_ancestors_basic(self) -> None:
        """Test getting ancestors of three-segment key."""
        key = ("users", "alice", "profile")
        ancestors = get_ancestors(key)
        # Ancestors includes parents up to but not including root
        assert ancestors == [("users",), ("users", "alice")]

    def test_get_ancestors_single_segment(self) -> None:
        """Test getting ancestors of single-segment key returns empty list."""
        key = ("users",)
        ancestors = get_ancestors(key)
        assert ancestors == []

    def test_get_ancestors_empty_key(self) -> None:
        """Test getting ancestors of empty key returns empty list."""
        key = ()
        ancestors = get_ancestors(key)
        assert ancestors == []

    def test_get_ancestors_two_segments(self) -> None:
        """Test getting ancestors of two-segment key."""
        key = ("users", "alice")
        ancestors = get_ancestors(key)
        assert ancestors == [("users",)]

    def test_get_ancestors_deep_key(self) -> None:
        """Test getting ancestors of deeply nested key."""
        key = ("a", "b", "c", "d")
        ancestors = get_ancestors(key)
        assert ancestors == [("a",), ("a", "b"), ("a", "b", "c")]

    def test_get_ancestors_order_from_root(self) -> None:
        """Test that ancestors are returned in order from root to parent."""
        key = ("x", "y", "z")
        ancestors = get_ancestors(key)
        # First ancestor should be one level deep
        assert ancestors[0] == ("x",)
        # Last ancestor should be immediate parent
        assert ancestors[-1] == ("x", "y")


class TestGetKeyChain:
    """Tests for get_key_chain function."""

    def test_get_key_chain_basic(self) -> None:
        """Test getting complete chain from ancestors to target."""
        key = ("users", "alice")
        chain = get_key_chain(key)
        # Chain is ancestors plus the key itself
        assert chain == [("users",), ("users", "alice")]

    def test_get_key_chain_single_segment(self) -> None:
        """Test getting chain of single-segment key."""
        key = ("users",)
        chain = get_key_chain(key)
        # For single segment, only the key itself is returned
        assert chain == [("users",)]

    def test_get_key_chain_empty_key(self) -> None:
        """Test getting chain of empty key."""
        key = ()
        chain = get_key_chain(key)
        assert chain == [()]

    def test_get_key_chain_includes_target(self) -> None:
        """Test that chain includes the target key."""
        key = ("users", "alice", "posts")
        chain = get_key_chain(key)
        assert chain[-1] == key

    def test_get_key_chain_three_segments(self) -> None:
        """Test that chain for three segments includes all levels."""
        key = ("users", "alice", "posts")
        chain = get_key_chain(key)
        # Should include ancestors plus target
        assert chain == [("users",), ("users", "alice"), ("users", "alice", "posts")]

    def test_get_key_chain_ordered(self) -> None:
        """Test that chain is properly ordered from root to target."""
        key = ("a", "b", "c")
        chain = get_key_chain(key)
        # Each element should be a prefix of the next
        for i in range(len(chain) - 1):
            assert chain[i] == chain[i + 1][: len(chain[i])]

    def test_get_key_chain_length(self) -> None:
        """Test that chain length equals key depth."""
        key = ("a", "b", "c", "d")
        chain = get_key_chain(key)
        # Chain length equals depth (not depth + 1, as no root)
        assert len(chain) == len(key)


class TestIsAncestor:
    """Tests for is_ancestor function."""

    def test_is_ancestor_direct_parent(self) -> None:
        """Test that direct parent is ancestor."""
        parent = ("users",)
        child = ("users", "alice")
        assert is_ancestor(parent, child)

    def test_is_ancestor_grandparent(self) -> None:
        """Test that grandparent is ancestor."""
        ancestor = ("users",)
        descendant = ("users", "alice", "posts")
        assert is_ancestor(ancestor, descendant)

    def test_is_ancestor_root(self) -> None:
        """Test that root is ancestor of all non-root keys."""
        ancestor = ()
        descendant = ("users", "alice")
        assert is_ancestor(ancestor, descendant)

    def test_is_ancestor_false_reverse(self) -> None:
        """Test that child is not ancestor of parent."""
        parent = ("users", "alice")
        child = ("users",)
        assert not is_ancestor(parent, child)

    def test_is_ancestor_false_siblings(self) -> None:
        """Test that siblings are not ancestors of each other."""
        key1 = ("users", "alice")
        key2 = ("users", "bob")
        assert not is_ancestor(key1, key2)
        assert not is_ancestor(key2, key1)

    def test_is_ancestor_false_different_branches(self) -> None:
        """Test keys in different branches are not ancestors."""
        key1 = ("users", "alice")
        key2 = ("posts", "1")
        assert not is_ancestor(key1, key2)

    def test_is_ancestor_false_equal_keys(self) -> None:
        """Test that key is not ancestor of itself."""
        key = ("users", "alice")
        assert not is_ancestor(key, key)

    def test_is_ancestor_empty_parent(self) -> None:
        """Test that empty key (root) is ancestor of any non-empty key."""
        assert is_ancestor((), ("a",))
        assert is_ancestor((), ("a", "b", "c"))


class TestIsDescendant:
    """Tests for is_descendant function."""

    def test_is_descendant_basic(self) -> None:
        """Test that descendant relationship is correctly identified."""
        child = ("users", "alice")
        parent = ("users",)
        assert is_descendant(child, parent)

    def test_is_descendant_deep(self) -> None:
        """Test descendant relationship across multiple levels."""
        descendant = ("users", "alice", "posts", "1")
        ancestor = ("users",)
        assert is_descendant(descendant, ancestor)

    def test_is_descendant_false_reversed(self) -> None:
        """Test that parent is not descendant of child."""
        parent = ("users",)
        child = ("users", "alice")
        assert not is_descendant(parent, child)

    def test_is_descendant_symmetry_with_is_ancestor(self) -> None:
        """Test that is_descendant is correct reverse of is_ancestor."""
        parent = ("a", "b")
        child = ("a", "b", "c", "d")
        assert is_descendant(child, parent) == is_ancestor(parent, child)


class TestIsSibling:
    """Tests for is_sibling function."""

    def test_is_sibling_basic(self) -> None:
        """Test that keys with same parent are siblings."""
        key1 = ("users", "alice")
        key2 = ("users", "bob")
        assert is_sibling(key1, key2)

    def test_is_sibling_symmetric(self) -> None:
        """Test that sibling relationship is symmetric."""
        key1 = ("users", "alice")
        key2 = ("users", "bob")
        assert is_sibling(key1, key2) == is_sibling(key2, key1)

    def test_is_sibling_false_parent_child(self) -> None:
        """Test that parent and child are not siblings."""
        parent = ("users",)
        child = ("users", "alice")
        assert not is_sibling(parent, child)

    def test_is_sibling_false_different_parents(self) -> None:
        """Test that keys with different parents are not siblings."""
        key1 = ("users", "alice")
        key2 = ("posts", "1")
        assert not is_sibling(key1, key2)

    def test_is_sibling_false_different_depths(self) -> None:
        """Test that keys at different depths are not siblings."""
        key1 = ("users", "alice")
        key2 = ("users", "alice", "profile")
        assert not is_sibling(key1, key2)

    def test_is_sibling_false_empty_keys(self) -> None:
        """Test that empty keys are not siblings."""
        key1 = ()
        key2 = ()
        assert not is_sibling(key1, key2)

    def test_is_sibling_single_segment_keys(self) -> None:
        """Test that single-segment keys with same parent are siblings.

        Single-segment keys have no parent, so they consider each other as siblings
        only if they share the same (empty) parent.
        """
        key1 = ("users",)
        key2 = ("posts",)
        # Both have length 1 and both have empty parent, so they are siblings
        assert is_sibling(key1, key2)

    def test_is_sibling_identical_keys(self) -> None:
        """Test that identical keys are considered siblings.

        Two identical keys have the same parent and depth, so they are siblings
        (they're the same key).
        """
        key = ("users", "alice")
        assert is_sibling(key, key)

    def test_is_sibling_deep_keys(self) -> None:
        """Test sibling relationship with deeply nested keys."""
        key1 = ("a", "b", "c", "d", "x")
        key2 = ("a", "b", "c", "d", "y")
        assert is_sibling(key1, key2)

    def test_is_sibling_with_integer_segments(self) -> None:
        """Test sibling relationship with integer segments."""
        key1 = ("items", 1)
        key2 = ("items", 2)
        assert is_sibling(key1, key2)


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


class TestGetCommonAncestor:
    """Tests for get_common_ancestor function."""

    def test_get_common_ancestor_basic(self) -> None:
        """Test finding common ancestor of related keys."""
        key1 = ("users", "alice", "posts")
        key2 = ("users", "bob")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ("users",)

    def test_get_common_ancestor_identical_keys(self) -> None:
        """Test common ancestor of identical keys is the key itself."""
        key = ("users", "alice", "posts")
        ancestor = get_common_ancestor(key, key)
        assert ancestor == key

    def test_get_common_ancestor_parent_child(self) -> None:
        """Test common ancestor of parent and child is parent."""
        parent = ("users", "alice")
        child = ("users", "alice", "posts")
        ancestor = get_common_ancestor(parent, child)
        assert ancestor == parent

    def test_get_common_ancestor_root(self) -> None:
        """Test common ancestor of unrelated keys is root."""
        key1 = ("users", "alice")
        key2 = ("posts", "1")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ()

    def test_get_common_ancestor_empty_keys(self) -> None:
        """Test common ancestor of empty keys is empty."""
        ancestor = get_common_ancestor((), ())
        assert ancestor == ()

    def test_get_common_ancestor_one_empty(self) -> None:
        """Test common ancestor when one key is empty."""
        key = ("users", "alice")
        ancestor = get_common_ancestor(key, ())
        assert ancestor == ()

    def test_get_common_ancestor_siblings(self) -> None:
        """Test common ancestor of siblings is their parent."""
        key1 = ("users", "alice")
        key2 = ("users", "bob")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ("users",)

    def test_get_common_ancestor_deep_keys(self) -> None:
        """Test finding common ancestor of deeply nested keys."""
        key1 = ("a", "b", "c", "d", "e")
        key2 = ("a", "b", "x", "y")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ("a", "b")

    def test_get_common_ancestor_single_segments(self) -> None:
        """Test common ancestor of single-segment keys."""
        key1 = ("users",)
        key2 = ("posts",)
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ()

    def test_get_common_ancestor_partial_match(self) -> None:
        """Test common ancestor stops at first difference."""
        key1 = ("a", "b", "x", "y", "z")
        key2 = ("a", "b", "c", "d", "e")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ("a", "b")
        # Should not include elements after the divergence
        assert len(ancestor) == 2

    def test_get_common_ancestor_with_integer_segments(self) -> None:
        """Test common ancestor with integer segments."""
        key1 = ("items", 1, "detail", 2)
        key2 = ("items", 1, "summary")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ("items", 1)

    def test_get_common_ancestor_different_first_segment(self) -> None:
        """Test common ancestor when first segments differ."""
        key1 = ("x", "a", "b")
        key2 = ("y", "a", "b")
        ancestor = get_common_ancestor(key1, key2)
        assert ancestor == ()


class TestIntegrationScenarios:
    """Integration tests combining multiple functions."""

    def test_scenario_tree_navigation(self) -> None:
        """Test complete tree navigation scenario."""
        # Create keys for a tree structure
        create_key()
        users = create_key("users")
        alice = create_key("users", "alice")
        alice_posts = create_key("users", "alice", "posts")

        # Verify hierarchy
        assert is_ancestor((), users)
        assert is_ancestor(users, alice)
        assert is_ancestor(alice, alice_posts)
        assert get_parent(alice_posts) == alice

    def test_scenario_metadata_tracking(self) -> None:
        """Test metadata key creation and conversion."""
        data_key = create_key("users", "alice")
        meta_key = to_meta(data_key)

        # Both should have same segments except root
        assert data_key[1:] == meta_key[1:]
        assert data_key[0] == DATA_ROOT
        assert meta_key[0] == METADATA_ROOT

    def test_scenario_key_relationships(self) -> None:
        """Test determining relationships between multiple keys."""
        key1 = ("org", "dept", "team", "alice")
        key2 = ("org", "dept", "team", "bob")
        key3 = ("org", "dept")

        # Alice and bob are siblings
        assert is_sibling(key1, key2)
        # Key3 is ancestor of both
        assert is_ancestor(key3, key1)
        assert is_ancestor(key3, key2)
        # Common ancestor of alice and bob is their parent
        assert get_common_ancestor(key1, key2) == ("org", "dept", "team")

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

    def test_scenario_full_hierarchy(self) -> None:
        """Test working with complete key hierarchy."""
        target = ("app", "config", "db", "host")

        # Get all levels
        chain = get_key_chain(target)
        ancestors = get_ancestors(target)

        # Verify consistency
        assert len(chain) == get_depth(target)  # Chain includes ancestors + target
        assert len(ancestors) == get_depth(target) - 1  # Ancestors exclude target
        assert [*ancestors, target] == chain
        assert chain[-1] == target

    def test_scenario_common_ancestor_multiple_paths(self) -> None:
        """Test finding common ancestor across complex paths."""
        key1 = ("company", "engineering", "frontend", "alice", "tasks")
        key2 = ("company", "engineering", "backend", "bob", "tasks")
        key3 = ("company", "marketing", "campaigns")

        # Common ancestor of frontend and backend
        ancestor_eng = get_common_ancestor(key1, key2)
        assert ancestor_eng == ("company", "engineering")

        # Common ancestor of engineering and marketing
        ancestor_company = get_common_ancestor(key1, key3)
        assert ancestor_company == ("company",)
