"""Path implementation for the state management system.

This module defines the Path class, which provides static utility methods
for manipulating hierarchical paths represented as tuples (TupleKey).

All methods work with raw tuples for maximum performance while providing
a clean namespace for path operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator

    from redwood.abc import KeyComponent, TupleKey


__all__ = ["Path"]


class Path:
    """Static utilities for TupleKey path manipulation.

    Path provides a collection of static methods for working with paths
    represented as tuples. All operations work directly on tuples without
    object instantiation overhead, providing maximum performance.

    Paths are represented as tuples where the first element is always a
    root marker, followed by path components.

    Example:
        ```python
        # Create a path tuple
        path = (Path.DATA_ROOT, "users", "alice", "profile")

        # Get the parent path
        parent_path = Path.parent(path)

        # Join with additional components
        extended_path = Path.join(path, "settings")

        # Get metadata path
        meta_path = Path.to_meta(path)
        ```
    """

    # Root marker for the root data component (stores actual data)
    DATA_ROOT: str = "/"
    # Root marker for the root structure component (stores tree structure)
    STRUCT_ROOT: str = "/s"
    # Root marker for the metadata component (stores metadata)
    METADATA_ROOT: str = "/m"

    @staticmethod
    def create(*components: KeyComponent, root: str | None = None) -> TupleKey:
        """Create a new path tuple with the given components.

        Args:
            *components: Path components after the root
            root: Root marker to use (defaults to DATA_ROOT)

        Returns:
            tuple: Path tuple with root marker and components

        Example:
            ```python
            path = Path.create("users", "alice", "profile")
            # Returns: ("/", "users", "alice", "profile")

            meta_path = Path.create("users", root=Path.METADATA_ROOT)
            # Returns: ("/m", "users")
            ```
        """
        if root is None:
            root = Path.DATA_ROOT
        return (root, *components)

    @staticmethod
    def root(root_marker: str | None = None) -> TupleKey:
        """Get a root path tuple.

        Args:
            root_marker: Root marker to use (defaults to DATA_ROOT)

        Returns:
            tuple: Root path tuple with only the root marker

        Example:
            ```python
            root = Path.root()  # Returns: ("/",)
            meta_root = Path.root(Path.METADATA_ROOT)  # Returns: ("/m",)
            ```
        """
        if root_marker is None:
            root_marker = Path.DATA_ROOT
        return (root_marker,)

    @staticmethod
    def components(path: TupleKey) -> TupleKey:
        """Get the path components without the root marker.

        Args:
            path: Path tuple

        Returns:
            tuple: Components without root marker

        Example:
            ```python
            path = ("/", "users", "alice")
            comps = Path.components(path)  # Returns: ("users", "alice")
            ```
        """
        return path[1:]

    @staticmethod
    def root_marker(path: TupleKey) -> str:
        """Get the root marker from a path.

        Args:
            path: Path tuple

        Returns:
            str: Root marker

        Example:
            ```python
            path = ("/", "users", "alice")
            marker = Path.root_marker(path)  # Returns: "/"
            ```
        """
        return path[0]  # type: ignore

    @staticmethod
    def join(base: TupleKey, *components: KeyComponent) -> TupleKey:
        """Create a new path by joining with additional components.

        Args:
            base: Base path tuple
            *components: Additional components to append

        Returns:
            tuple: New path with combined components

        Example:
            ```python
            path = ("/", "users")
            user_path = Path.join(path, "alice", "profile")
            # Returns: ("/", "users", "alice", "profile")
            ```
        """
        return base + components

    @staticmethod
    def parent(path: TupleKey) -> TupleKey | None:
        """Get the parent path.

        Args:
            path: Path tuple

        Returns:
            tuple | None: Parent path, or None if this is the root path

        Example:
            ```python
            path = ("/", "users", "alice")
            parent = Path.parent(path)  # Returns: ("/", "users")

            root = ("/",)
            parent = Path.parent(root)  # Returns: None
            ```
        """
        if len(path) <= 1:
            # This is the root path
            return None
        return path[:-1]

    @staticmethod
    def last(path: TupleKey) -> KeyComponent | None:
        """Get the last component of the path.

        Args:
            path: Path tuple

        Returns:
            str | int | None: Last component, or None if this is the root

        Example:
            ```python
            path = ("/", "users", "alice")
            last = Path.last(path)  # Returns: "alice"

            root = ("/",)
            last = Path.last(root)  # Returns: None
            ```
        """
        if len(path) <= 1:
            # This is the root path
            return None
        return path[-1]

    @staticmethod
    def is_root(path: TupleKey) -> bool:
        """Check if this is a root path.

        Args:
            path: Path tuple

        Returns:
            bool: True if this is the root path (only has root marker)

        Example:
            ```python
            root = ("/",)
            is_root = Path.is_root(root)  # Returns: True

            path = ("/", "users")
            is_root = Path.is_root(path)  # Returns: False
            ```
        """
        return len(path) == 1

    @staticmethod
    def length(path: TupleKey) -> int:
        """Get the number of components in the path (excluding root).

        Args:
            path: Path tuple

        Returns:
            int: Number of components

        Example:
            ```python
            path = ("/", "users", "alice")
            length = Path.length(path)  # Returns: 2
            ```
        """
        return len(path) - 1

    @staticmethod
    def is_ancestor_of(ancestor: TupleKey, path: TupleKey) -> bool:
        """Check if ancestor is an ancestor of path.

        Args:
            ancestor: Potential ancestor path
            path: Path to check

        Returns:
            bool: True if ancestor is an ancestor of path

        Example:
            ```python
            users = ("/", "users")
            alice = ("/", "users", "alice")
            is_ancestor = Path.is_ancestor_of(users, alice)  # Returns: True
            ```
        """
        if len(ancestor) >= len(path):
            return False
        return path[: len(ancestor)] == ancestor

    @staticmethod
    def is_descendant_of(path: TupleKey, ancestor: TupleKey) -> bool:
        """Check if path is a descendant of ancestor.

        Args:
            path: Path to check
            ancestor: Potential ancestor path

        Returns:
            bool: True if path is a descendant of ancestor

        Example:
            ```python
            users = ("/", "users")
            alice = ("/", "users", "alice")
            is_descendant = Path.is_descendant_of(alice, users)  # Returns: True
            ```
        """
        return Path.is_ancestor_of(ancestor, path)

    @staticmethod
    def relative_to(path: TupleKey, ancestor: TupleKey) -> TupleKey | None:
        """Get the relative path from an ancestor path to this path.

        Args:
            path: Path to get relative version of
            ancestor: Ancestor path

        Returns:
            tuple | None: Relative path with same root marker, or None if not a descendant

        Example:
            ```python
            users = ("/", "users")
            alice_profile = ("/", "users", "alice", "profile")
            relative = Path.relative_to(alice_profile, users)
            # Returns: ("/", "alice", "profile")
            ```
        """
        if not Path.is_descendant_of(path, ancestor):
            return None

        # Get components after the ancestor and preserve root marker
        root_marker = path[0]
        relative_components = path[len(ancestor) :]
        return (root_marker, *relative_components)

    @staticmethod
    def to_string(path: TupleKey) -> str:
        """Convert path to a string representation.

        Args:
            path: Path tuple

        Returns:
            str: Path as a string with '/' separator

        Example:
            ```python
            path = ("/", "users", "alice")
            s = Path.to_string(path)  # Returns: "/users/alice"
            ```
        """
        if len(path) == 1:
            # Just the root
            return str(path[0])

        root = path[0]
        components = path[1:]
        return str(root) + "/".join(str(comp) for comp in components)

    @staticmethod
    def to_meta(path: TupleKey) -> TupleKey:
        """Convert a path to its metadata equivalent.

        Args:
            path: Path tuple

        Returns:
            tuple: New path with metadata root marker

        Example:
            ```python
            path = ("/", "users", "alice")
            meta = Path.to_meta(path)  # Returns: ("/m", "users", "alice")
            ```
        """
        return (Path.METADATA_ROOT, *path[1:])

    @staticmethod
    def to_struct(path: TupleKey) -> TupleKey:
        """Convert a path to its structure equivalent.

        Args:
            path: Path tuple

        Returns:
            tuple: New path with structure root marker

        Example:
            ```python
            path = ("/", "users", "alice")
            struct = Path.to_struct(path)  # Returns: ("/s", "users", "alice")
            ```
        """
        return (Path.STRUCT_ROOT, *path[1:])

    @staticmethod
    def to_data(path: TupleKey) -> TupleKey:
        """Convert a path to its data equivalent.

        Args:
            path: Path tuple

        Returns:
            tuple: New path with data root marker

        Example:
            ```python
            meta = ("/m", "users", "alice")
            data = Path.to_data(meta)  # Returns: ("/", "users", "alice")
            ```
        """
        return (Path.DATA_ROOT, *path[1:])

    @staticmethod
    def ancestors(path: TupleKey) -> Iterator[TupleKey]:
        """Get all ancestor paths from root to parent.

        Args:
            path: Path tuple

        Yields:
            tuple: Ancestor paths from root to immediate parent

        Example:
            ```python
            path = ("/", "users", "alice", "profile")
            for ancestor in Path.ancestors(path):
                print(ancestor)
            # Prints:
            # ("/",)
            # ("/", "users")
            # ("/", "users", "alice")
            ```
        """
        for i in range(1, len(path)):
            yield path[:i]

    @staticmethod
    def descendants_depth(path: TupleKey, depth: int) -> TupleKey:
        """Get a descendant path at a specific depth relative to the given path.

        Note: This creates a path structure but doesn't validate if it exists.

        Args:
            path: Base path tuple
            depth: Number of levels deep (must be positive)

        Returns:
            tuple: Path extended with placeholder components

        Example:
            ```python
            path = ("/", "users")
            deep = Path.descendants_depth(path, 2)
            # Returns: ("/", "users", "*", "*")
            ```
        """
        if depth < 0:
            raise ValueError("Depth must be non-negative")
        return path + ("*",) * depth

    @staticmethod
    def common_ancestor(path1: TupleKey, path2: TupleKey) -> TupleKey | None:
        """Find the common ancestor of two paths.

        Args:
            path1: First path tuple
            path2: Second path tuple

        Returns:
            tuple | None: Longest common ancestor path, or None if no common ancestor

        Example:
            ```python
            alice = ("/", "users", "alice", "profile")
            bob = ("/", "users", "bob", "settings")
            common = Path.common_ancestor(alice, bob)
            # Returns: ("/", "users")
            ```
        """
        # Must have same root marker
        if path1[0] != path2[0]:
            return None

        # Find common prefix
        min_len = min(len(path1), len(path2))
        common_len = 1  # At least the root

        for i in range(1, min_len):
            if path1[i] == path2[i]:
                common_len = i + 1
            else:
                break

        return path1[:common_len]
