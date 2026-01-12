"""Unit tests for the site_nav module - site traversal and navigation operations.

This test module covers hierarchical site manipulation functions:
- Parent/ancestor relationships
- Descendant checks
- Sibling relationships
- Site chain construction

For flat key operations (construction, joining), see test_loc_key_nav.py.
"""

from everyshape.loc.site import (
    get_ancestors,
    get_common_ancestor,
    get_depth,
    get_parent,
    get_site_chain,
    is_ancestor,
    is_descendant,
    is_root,
    is_sibling,
    join_segment,
)


class TestGetParent:
    """Tests for get_parent function."""

    def test_get_parent_basic(self) -> None:
        """Test getting parent of simple site."""
        site = ("users", "alice")
        parent = get_parent(site)
        assert parent == ("users",)

    def test_get_parent_single_segment(self) -> None:
        """Test getting parent of single-segment site returns empty tuple."""
        site = ("users",)
        parent = get_parent(site)
        assert parent == ()

    def test_get_parent_empty_site(self) -> None:
        """Test getting parent of empty site returns None."""
        site = ()
        parent = get_parent(site)
        assert parent is None

    def test_get_parent_deep_site(self) -> None:
        """Test getting parent of deeply nested site."""
        site = ("a", "b", "c", "d", "e")
        parent = get_parent(site)
        assert parent == ("a", "b", "c", "d")


class TestGetAncestors:
    """Tests for get_ancestors function."""

    def test_get_ancestors_basic(self) -> None:
        """Test getting ancestors of three-segment site."""
        site = ("users", "alice", "profile")
        ancestors = get_ancestors(site)
        assert ancestors == [("users",), ("users", "alice")]

    def test_get_ancestors_single_segment(self) -> None:
        """Test getting ancestors of single-segment site returns empty list."""
        site = ("users",)
        ancestors = get_ancestors(site)
        assert ancestors == []

    def test_get_ancestors_empty_site(self) -> None:
        """Test getting ancestors of empty site returns empty list."""
        site = ()
        ancestors = get_ancestors(site)
        assert ancestors == []

    def test_get_ancestors_two_segments(self) -> None:
        """Test getting ancestors of two-segment site."""
        site = ("users", "alice")
        ancestors = get_ancestors(site)
        assert ancestors == [("users",)]

    def test_get_ancestors_deep_site(self) -> None:
        """Test getting ancestors of deeply nested site."""
        site = ("a", "b", "c", "d")
        ancestors = get_ancestors(site)
        assert ancestors == [("a",), ("a", "b"), ("a", "b", "c")]

    def test_get_ancestors_order_from_root(self) -> None:
        """Test that ancestors are returned in order from root to parent."""
        site = ("x", "y", "z")
        ancestors = get_ancestors(site)
        # First ancestor should be one level deep
        assert ancestors[0] == ("x",)
        # Last ancestor should be immediate parent
        assert ancestors[-1] == ("x", "y")


class TestGetSiteChain:
    """Tests for get_site_chain function."""

    def test_get_site_chain_basic(self) -> None:
        """Test getting complete chain from ancestors to target."""
        site = ("users", "alice")
        chain = get_site_chain(site)
        assert chain == [("users",), ("users", "alice")]

    def test_get_site_chain_single_segment(self) -> None:
        """Test getting chain of single-segment site."""
        site = ("users",)
        chain = get_site_chain(site)
        assert chain == [("users",)]

    def test_get_site_chain_empty_site(self) -> None:
        """Test getting chain of empty site."""
        site = ()
        chain = get_site_chain(site)
        assert chain == [()]

    def test_get_site_chain_includes_target(self) -> None:
        """Test that chain includes the target site."""
        site = ("users", "alice", "posts")
        chain = get_site_chain(site)
        assert chain[-1] == site

    def test_get_site_chain_three_segments(self) -> None:
        """Test that chain for three segments includes all levels."""
        site = ("users", "alice", "posts")
        chain = get_site_chain(site)
        assert chain == [("users",), ("users", "alice"), ("users", "alice", "posts")]

    def test_get_site_chain_ordered(self) -> None:
        """Test that chain is properly ordered from root to target."""
        site = ("a", "b", "c")
        chain = get_site_chain(site)
        # Each element should be a prefix of the next
        for i in range(len(chain) - 1):
            assert chain[i] == chain[i + 1][: len(chain[i])]

    def test_get_site_chain_length(self) -> None:
        """Test that chain length equals site depth."""
        site = ("a", "b", "c", "d")
        chain = get_site_chain(site)
        assert len(chain) == len(site)


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
        """Test that root is ancestor of all non-root sites."""
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
        site1 = ("users", "alice")
        site2 = ("users", "bob")
        assert not is_ancestor(site1, site2)
        assert not is_ancestor(site2, site1)

    def test_is_ancestor_false_different_branches(self) -> None:
        """Test sites in different branches are not ancestors."""
        site1 = ("users", "alice")
        site2 = ("posts", "1")
        assert not is_ancestor(site1, site2)

    def test_is_ancestor_false_equal_sites(self) -> None:
        """Test that site is not ancestor of itself."""
        site = ("users", "alice")
        assert not is_ancestor(site, site)

    def test_is_ancestor_empty_parent(self) -> None:
        """Test that empty site (root) is ancestor of any non-empty site."""
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
        """Test that sites with same parent are siblings."""
        site1 = ("users", "alice")
        site2 = ("users", "bob")
        assert is_sibling(site1, site2)

    def test_is_sibling_symmetric(self) -> None:
        """Test that sibling relationship is symmetric."""
        site1 = ("users", "alice")
        site2 = ("users", "bob")
        assert is_sibling(site1, site2) == is_sibling(site2, site1)

    def test_is_sibling_false_parent_child(self) -> None:
        """Test that parent and child are not siblings."""
        parent = ("users",)
        child = ("users", "alice")
        assert not is_sibling(parent, child)

    def test_is_sibling_false_different_parents(self) -> None:
        """Test that sites with different parents are not siblings."""
        site1 = ("users", "alice")
        site2 = ("posts", "1")
        assert not is_sibling(site1, site2)

    def test_is_sibling_false_different_depths(self) -> None:
        """Test that sites at different depths are not siblings."""
        site1 = ("users", "alice")
        site2 = ("users", "alice", "profile")
        assert not is_sibling(site1, site2)

    def test_is_sibling_false_empty_sites(self) -> None:
        """Test that empty sites are not siblings."""
        site1 = ()
        site2 = ()
        assert not is_sibling(site1, site2)

    def test_is_sibling_single_segment_sites(self) -> None:
        """Test that single-segment sites with same parent are siblings."""
        site1 = ("users",)
        site2 = ("posts",)
        assert is_sibling(site1, site2)

    def test_is_sibling_identical_sites(self) -> None:
        """Test that identical sites are considered siblings."""
        site = ("users", "alice")
        assert is_sibling(site, site)

    def test_is_sibling_deep_sites(self) -> None:
        """Test sibling relationship with deeply nested sites."""
        site1 = ("a", "b", "c", "d", "x")
        site2 = ("a", "b", "c", "d", "y")
        assert is_sibling(site1, site2)

    def test_is_sibling_with_integer_segments(self) -> None:
        """Test sibling relationship with integer segments."""
        site1 = ("items", 1)
        site2 = ("items", 2)
        assert is_sibling(site1, site2)


class TestIsRoot:
    """Tests for is_root function."""

    def test_is_root_empty(self) -> None:
        """Test that empty tuple is root."""
        assert is_root(())

    def test_is_root_single_segment(self) -> None:
        """Test that single-segment is root level."""
        assert is_root(("users",))

    def test_is_root_two_segments(self) -> None:
        """Test that two-segment is not root."""
        assert not is_root(("users", "alice"))


class TestGetDepth:
    """Tests for get_depth function."""

    def test_get_depth_empty_site(self) -> None:
        """Test depth of empty site is 0."""
        assert get_depth(()) == 0

    def test_get_depth_single_segment(self) -> None:
        """Test depth of single-segment site is 1."""
        assert get_depth(("users",)) == 1

    def test_get_depth_two_segments(self) -> None:
        """Test depth of two-segment site is 2."""
        assert get_depth(("users", "alice")) == 2

    def test_get_depth_multiple_segments(self) -> None:
        """Test depth equals number of segments."""
        site = ("a", "b", "c", "d", "e")
        assert get_depth(site) == 5


class TestJoinSegment:
    """Tests for join_segment function."""

    def test_join_segment_basic(self) -> None:
        """Test appending segment to site."""
        site = ("users",)
        result = join_segment(site, "alice")
        assert result == ("users", "alice")

    def test_join_segment_multiple(self) -> None:
        """Test appending multiple segments to site."""
        site = ("users",)
        result = join_segment(site, "alice", "posts")
        assert result == ("users", "alice", "posts")

    def test_join_segment_to_empty_site(self) -> None:
        """Test appending segment to empty site."""
        site = ()
        result = join_segment(site, "users")
        assert result == ("users",)


class TestGetCommonAncestor:
    """Tests for get_common_ancestor function."""

    def test_get_common_ancestor_basic(self) -> None:
        """Test finding common ancestor of related sites."""
        site1 = ("users", "alice", "posts")
        site2 = ("users", "bob")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ("users",)

    def test_get_common_ancestor_identical_sites(self) -> None:
        """Test common ancestor of identical sites is the site itself."""
        site = ("users", "alice", "posts")
        ancestor = get_common_ancestor(site, site)
        assert ancestor == site

    def test_get_common_ancestor_parent_child(self) -> None:
        """Test common ancestor of parent and child is parent."""
        parent = ("users", "alice")
        child = ("users", "alice", "posts")
        ancestor = get_common_ancestor(parent, child)
        assert ancestor == parent

    def test_get_common_ancestor_root(self) -> None:
        """Test common ancestor of unrelated sites is root."""
        site1 = ("users", "alice")
        site2 = ("posts", "1")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ()

    def test_get_common_ancestor_empty_sites(self) -> None:
        """Test common ancestor of empty sites is empty."""
        ancestor = get_common_ancestor((), ())
        assert ancestor == ()

    def test_get_common_ancestor_one_empty(self) -> None:
        """Test common ancestor when one site is empty."""
        site = ("users", "alice")
        ancestor = get_common_ancestor(site, ())
        assert ancestor == ()

    def test_get_common_ancestor_siblings(self) -> None:
        """Test common ancestor of siblings is their parent."""
        site1 = ("users", "alice")
        site2 = ("users", "bob")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ("users",)

    def test_get_common_ancestor_deep_sites(self) -> None:
        """Test finding common ancestor of deeply nested sites."""
        site1 = ("a", "b", "c", "d", "e")
        site2 = ("a", "b", "x", "y")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ("a", "b")

    def test_get_common_ancestor_single_segments(self) -> None:
        """Test common ancestor of single-segment sites."""
        site1 = ("users",)
        site2 = ("posts",)
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ()

    def test_get_common_ancestor_partial_match(self) -> None:
        """Test common ancestor stops at first difference."""
        site1 = ("a", "b", "x", "y", "z")
        site2 = ("a", "b", "c", "d", "e")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ("a", "b")
        assert len(ancestor) == 2

    def test_get_common_ancestor_with_integer_segments(self) -> None:
        """Test common ancestor with integer segments."""
        site1 = ("items", 1, "detail", 2)
        site2 = ("items", 1, "summary")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ("items", 1)

    def test_get_common_ancestor_different_first_segment(self) -> None:
        """Test common ancestor when first segments differ."""
        site1 = ("x", "a", "b")
        site2 = ("y", "a", "b")
        ancestor = get_common_ancestor(site1, site2)
        assert ancestor == ()


class TestIntegrationScenarios:
    """Integration tests combining multiple functions."""

    def test_scenario_tree_navigation(self) -> None:
        """Test complete tree navigation scenario."""
        users = ("users",)
        alice = ("users", "alice")
        alice_posts = ("users", "alice", "posts")

        # Verify hierarchy
        assert is_ancestor((), users)
        assert is_ancestor(users, alice)
        assert is_ancestor(alice, alice_posts)
        assert get_parent(alice_posts) == alice

    def test_scenario_site_relationships(self) -> None:
        """Test determining relationships between multiple sites."""
        site1 = ("org", "dept", "team", "alice")
        site2 = ("org", "dept", "team", "bob")
        site3 = ("org", "dept")

        # Alice and bob are siblings
        assert is_sibling(site1, site2)
        # site3 is ancestor of both
        assert is_ancestor(site3, site1)
        assert is_ancestor(site3, site2)
        # Common ancestor of alice and bob is their parent
        assert get_common_ancestor(site1, site2) == ("org", "dept", "team")

    def test_scenario_full_hierarchy(self) -> None:
        """Test working with complete site hierarchy."""
        target = ("app", "config", "db", "host")

        # Get all levels
        chain = get_site_chain(target)
        ancestors = get_ancestors(target)

        # Verify consistency
        assert len(chain) == get_depth(target)
        assert len(ancestors) == get_depth(target) - 1
        assert [*ancestors, target] == chain
        assert chain[-1] == target

    def test_scenario_common_ancestor_multiple_paths(self) -> None:
        """Test finding common ancestor across complex paths."""
        site1 = ("company", "engineering", "frontend", "alice", "tasks")
        site2 = ("company", "engineering", "backend", "bob", "tasks")
        site3 = ("company", "marketing", "campaigns")

        # Common ancestor of frontend and backend
        ancestor_eng = get_common_ancestor(site1, site2)
        assert ancestor_eng == ("company", "engineering")

        # Common ancestor of engineering and marketing
        ancestor_company = get_common_ancestor(site1, site3)
        assert ancestor_company == ("company",)
