"""Site traversal and navigation operations.

This module provides hierarchical site manipulation functions for the Container layer.
Sites represent hierarchical locations with parent-child relationships.

All functions are pure (no storage access), stateless, and can be safely cached.

Key vs Site semantics:
    - Key: flat storage coordinates, join operations
    - Site: hierarchical place, ancestor/descendant relationships

Performance notes:
    - All operations are pure functions on tuples
    - Heavy use of tuple slicing which is highly optimized in CPython
    - Short-circuit evaluation for boolean checks
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .site import Site, SiteSegment

__all__ = [
    "get_ancestors",
    "get_common_ancestor",
    "get_depth",
    "get_parent",
    "get_site_chain",
    "is_ancestor",
    "is_descendant",
    "is_root",
    "is_sibling",
    "join_segment",
    "to_child",
]


def get_parent(site: Site) -> Site | None:
    """Get parent site.

    Args:
        site: Site to get parent of

    Returns:
        Parent site, or None if site is empty (root has no parent)

    Example:
        >>> get_parent(("users", "alice"))
        ("users",)
        >>> get_parent(("users",))
        ()
        >>> get_parent(())
        None
    """
    if not site:
        return None

    return site[:-1]


def get_ancestors(site: Site) -> list[Site]:
    """Get all ancestors from root to immediate parent.

    Returns ancestors in order from root to immediate parent.
    Does not include the site itself.

    Args:
        site: Site to get ancestors of

    Returns:
        List of ancestor sites, empty list for root

    Example:
        >>> get_ancestors(("users", "alice", "profile"))
        [("users",), ("users", "alice")]
        >>> get_ancestors(("users",))
        []
        >>> get_ancestors(())
        []
    """
    if len(site) <= 1:
        return []

    ancestors = []
    current = site[:-1]  # Start with immediate parent

    while current:  # Stop when current is empty tuple (root)
        ancestors.append(current)
        current = current[:-1] if current else None

    return list(reversed(ancestors))


def get_site_chain(site: Site) -> list[Site]:
    """Get complete site chain from root to target.

    Returns all sites from root to target, including the target itself.

    Args:
        site: Target site

    Returns:
        List of sites from root to target (inclusive)

    Example:
        >>> get_site_chain(("users", "alice"))
        [("users",), ("users", "alice")]
        >>> get_site_chain(("users",))
        [("users",)]
        >>> get_site_chain(())
        [()]
    """
    if not site:
        return [()]

    chain = get_ancestors(site)
    chain.append(site)
    return chain


def is_ancestor(ancestor: Site, descendant: Site) -> bool:
    """Check if one site is an ancestor of another.

    A site is considered an ancestor if it's a prefix of the descendant site
    and strictly shorter.

    Args:
        ancestor: Potential ancestor site
        descendant: Potential descendant site

    Returns:
        True if ancestor is an ancestor of descendant

    Example:
        >>> is_ancestor(("users",), ("users", "alice"))
        True
        >>> is_ancestor(("users", "alice"), ("users",))
        False
        >>> is_ancestor(("users",), ("users",))
        False
        >>> is_ancestor((), ("users",))
        True
    """
    # Hot site optimization: check length first (cheap), then slice (more expensive)
    return len(ancestor) < len(descendant) and descendant[: len(ancestor)] == ancestor


def is_descendant(descendant: Site, ancestor: Site) -> bool:
    """Check if one site is a descendant of another.

    Convenience wrapper around is_ancestor with reversed arguments.

    Args:
        descendant: Potential descendant site
        ancestor: Potential ancestor site

    Returns:
        True if descendant is a descendant of ancestor

    Example:
        >>> is_descendant(("users", "alice"), ("users",))
        True
        >>> is_descendant(("users",), ("users", "alice"))
        False
    """
    return is_ancestor(ancestor, descendant)


def is_sibling(site1: Site, site2: Site) -> bool:
    """Check if two sites are siblings.

    Siblings share the same parent site and are at the same depth.

    Args:
        site1: First site
        site2: Second site

    Returns:
        True if sites are siblings

    Example:
        >>> is_sibling(("users", "alice"), ("users", "bob"))
        True
        >>> is_sibling(("users", "alice"), ("posts", "1"))
        False
        >>> is_sibling(("users",), ("posts",))
        True
    """
    # Must be same depth (non-zero) and same parent
    if not site1 or not site2:
        return False
    if len(site1) != len(site2):
        return False
    return site1[:-1] == site2[:-1]


def is_root(site: Site) -> bool:
    """Check if site is the root.

    The root site is either an empty tuple or a single-segment tuple
    (e.g., the data root marker).

    Args:
        site: Site to check

    Returns:
        True if site is root level

    Example:
        >>> is_root(())
        True
        >>> is_root(("/",))
        True
        >>> is_root(("users",))
        True
        >>> is_root(("users", "alice"))
        False
    """
    return len(site) <= 1


def get_depth(site: Site) -> int:
    """Get depth of site in the hierarchy.

    Depth is the number of segments in the site. Root (empty tuple) has depth 0.

    Args:
        site: Site to measure

    Returns:
        Depth (length) of site

    Example:
        >>> get_depth(())
        0
        >>> get_depth(("users",))
        1
        >>> get_depth(("users", "alice"))
        2
    """
    return len(site)


def get_common_ancestor(site1: Site, site2: Site) -> Site:
    """Find lowest common ancestor of two sites.

    Returns the deepest site that is an ancestor of both input sites.

    Args:
        site1: First site
        site2: Second site

    Returns:
        Common ancestor site (may be empty tuple for root)

    Example:
        >>> get_common_ancestor(("users", "alice", "posts"), ("users", "bob"))
        ("users",)
        >>> get_common_ancestor(("users", "alice"), ("posts", "1"))
        ()
        >>> get_common_ancestor(("users", "alice"), ("users", "alice", "profile"))
        ("users", "alice")
    """
    # Find common prefix
    min_len = min(len(site1), len(site2))
    common_len = 0

    for i in range(min_len):
        if site1[i] == site2[i]:
            common_len = i + 1
        else:
            break

    return site1[:common_len]


def to_child(site: Site, *segments: SiteSegment) -> Site:
    """Navigate to child site by appending segments.

    Creates a child site by appending one or more segments to the parent site.
    This is a hierarchical navigation operation.

    Args:
        site: Parent site
        *segments: Child segments to navigate to

    Returns:
        Child site with segments appended

    Example:
        >>> to_child(("users",), "alice")
        ("users", "alice")
        >>> to_child(("users", "alice"), "profile", "settings")
        ("users", "alice", "profile", "settings")
        >>> to_child((), "users")
        ("users",)
    """
    return site + segments


# Backward-compatible alias
join_segment = to_child
