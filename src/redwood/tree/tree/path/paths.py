"""Path implementation for the state management system.

This module defines the Path class, which represents a hierarchical path
in the state tree and provides methods for path manipulation and navigation.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Self


if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..types import PathComponent


__all__ = ["Path"]


class Path:
    """Represents a hierarchical path in the state tree.

    Path handles the representation and manipulation of paths for navigating
    through the state tree. It provides methods for joining paths, getting parent
    paths, and other path operations similar to filesystem paths.

    A Path always has a root component, ensuring proper hierarchical organization.

    Example:
        ```python
        # Create a path with components
        path = Path("users", "alice", "profile")

        # Get the parent path
        parent_path = path.parent()

        # Join with additional components
        extended_path = path.join("settings")
        ```
    """

    # Root marker for the root data component (stores actual data)
    DATA_ROOT_MARKER: str = "/"
    # Root marker for the root structure component (stores tree structure)
    STRUCT_ROOT_MARKER: str = "/s"
    # Root marker for the metadata component (stores metadata)
    METADATA_ROOT_MARKER: str = "/m"

    @cached_property
    def root_marker(self) -> str:
        """Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        return self.DATA_ROOT_MARKER

    @cached_property
    def struct_path(self) -> StructPath:
        """Get the path for the structure component.

        Returns:
            StructPath: New path with structure root marker
        """
        return StructPath(*self.components)

    @cached_property
    def meta_path(self) -> MetaPath:
        """Get the path for the metadata component.

        Returns:
            MetaPath: New path with metadata root marker
        """
        return MetaPath(*self.components)

    def __init__(self, *components: PathComponent) -> None:
        """Initialize a path with the given components.

        Always includes a root component as the first element.

        Args:
            *components: Path components after the root
        """
        self._components = (self.root_marker, *tuple(components))

    @cached_property
    def components(self) -> tuple[PathComponent, ...]:
        """Get the path components as a tuple.

        Returns:
            tuple[PathComponent, ...]: Path components including root
        """
        return self._components[1:]

    def to_tuple(self) -> tuple[PathComponent, ...]:
        """Get the path as a tuple for use with the backend.

        Returns:
            tuple[PathComponent, ...]: Path components as a tuple
        """
        return self._components

    def __str__(self) -> str:
        """Convert path to a string representation.

        Returns:
            str: Path as a string with '/' separator
        """
        if len(self.components) == 0:
            # Just the root
            return self.root_marker

        return self.root_marker + "/".join(str(comp) for comp in self.components)

    def __repr__(self) -> str:
        """Get a detailed string representation for debugging.

        Returns:
            str: Detailed representation of the path
        """
        if len(self) == 0:
            return f"{self.__class__.__name__}()"

        return f"{self.__class__.__name__}({', '.join(repr(c) for c in self.components)})"

    def __eq__(self, other: object) -> bool:
        """Check if two paths are equal.

        Args:
            other: Another object to compare with

        Returns:
            bool: True if paths have the same components
        """
        if not isinstance(other, type(self)):
            return False
        return self._components == other._components

    def __hash__(self) -> int:
        """Get hash value for the path.

        Returns:
            int: Hash based on path components
        """
        return hash(self._components)

    def __len__(self) -> int:
        """Get the number of components in the path (including root).

        Returns:
            int: Number of components
        """
        return len(self.components)

    def __iter__(self) -> Iterator[PathComponent]:
        """Get an iterator over the path components.

        Returns:
            Iterator[PathComponent]: Iterator over components
        """
        return iter(self.components)

    def join(self, *components: PathComponent) -> Self:
        """Create a new path by joining with additional components.

        Args:
            *components: Additional components to append

        Returns:
            Path: New path with combined components

        Example:
            ```python
            path = Path("users")
            user_path = path.join("alice", "profile")
            ```
        """
        return self.__class__(*self.components, *components)

    def parent(self) -> Self | None:
        """Get the parent path.

        Returns:
            Path: Parent path, or None if this is the root path

        Example:
            ```python
            path = Path("users", "alice")
            parent = path.parent()  # Path("users")
            ```
        """
        if len(self.components) == 0:
            # This is the root path
            return None

        return self.__class__(*self.components[:-1])

    def last(self) -> PathComponent | None:
        """Get the last component of the path.

        Returns:
            PathComponent: Last component

        Example:
            ```python
            path = Path("users", "alice")
            last = path.last()  # "alice"
            ```
        """
        if len(self.components) == 0:
            # This is the root path
            return None

        return self.components[-1]

    def root(self) -> Self:
        """Get the root path.

        Returns:
            Path: Root path (only root component)
        """
        return self.__class__()

    def is_root(self) -> bool:
        """Check if this is the root path.

        Returns:
            bool: True if this is the root path (only has root component)

        Example:
            ```python
            root = Path()
            is_root = root.is_root()  # True
            ```
        """
        return len(self.components) == 0

    def is_ancestor_of(self, other: Path) -> bool:
        """Check if this path is an ancestor of another path.

        Args:
            other: Path to check against

        Returns:
            bool: True if this path is an ancestor of other

        Example:
            ```python
            users = Path("users")
            alice = Path("users", "alice")
            is_ancestor = users.is_ancestor_of(alice)  # True
            ```
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Expected {type(self).__name__}, got {type(other).__name__}")

        if len(self._components) >= len(other._components):
            return False

        # Check if all components match up to the length of self
        return other._components[: len(self._components)] == self._components

    def is_descendant_of(self, other: Path) -> bool:
        """Check if this path is a descendant of another path.

        Args:
            other: Path to check against

        Returns:
            bool: True if this path is a descendant of other

        Example:
            ```python
            users = Path("users")
            alice = Path("users", "alice")
            is_descendant = alice.is_descendant_of(users)  # True
            ```
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Expected {type(self).__name__}, got {type(other).__name__}")

        return other.is_ancestor_of(self)

    def relative_to(self, ancestor: Path) -> Self | None:
        """Get the relative path from an ancestor path to this path.

        Args:
            ancestor: Ancestor path

        Returns:
            Path: Relative path, or None if not a descendant

        Example:
            ```python
            users = Path("users")
            alice_profile = Path("users", "alice", "profile")
            relative = alice_profile.relative_to(users)  # Path("alice", "profile")
            ```
        """
        if not isinstance(ancestor, type(self)):
            raise TypeError(f"Expected {type(self).__name__}, got {type(ancestor).__name__}")

        if not self.is_descendant_of(ancestor):
            return None

        # Get components after the ancestor
        relative_components = self._components[len(ancestor._components) :]
        return self.__class__(*relative_components)


class StructPath(Path):
    @cached_property
    def root_marker(self) -> str:
        """Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        return self.STRUCT_ROOT_MARKER


class MetaPath(Path):
    @cached_property
    def root_marker(self) -> str:
        """Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        return self.METADATA_ROOT_MARKER
