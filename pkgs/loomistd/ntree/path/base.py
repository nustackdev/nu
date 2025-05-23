"""
Path implementation for the state management system.

This module defines the StatePath class, which represents a hierarchical path
in the state tree and provides methods for path manipulation and navigation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, Self

from ..types import PathComponent

__all__ = ["StatePath"]


class StatePath(ABC):
    """
    Represents a hierarchical path in the state tree.

    StatePath handles the representation and manipulation of paths for navigating
    through the state tree. It provides methods for joining paths, getting parent
    paths, and other path operations similar to filesystem paths.

    A StatePath always has a root component, ensuring proper hierarchical organization.

    Example:
        ```python
        # Create a path with components
        path = StatePath("users", "alice", "profile")

        # Get the parent path
        parent_path = path.parent()

        # Join with additional components
        extended_path = path.join("settings")

        # Create a path from a string
        from_str = StatePath.from_string("/users/alice")
        ```
    """

    # Root marker for the root data component (stores actual data)
    DATA_ROOT_MARKER: str = "/"
    # Root marker for the root structure component (stores tree structure)
    STRUCT_ROOT_MARKER: str = "/s"

    @property
    @abstractmethod
    def root_marker(self) -> str:
        """
        Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        raise NotImplementedError("Subclasses must implement root_marker property")

    def __init__(self, *components: PathComponent) -> None:
        """
        Initialize a path with the given components.

        Always includes a root component as the first element.

        Args:
            *components: Path components after the root
        """
        self._components = (self.root_marker,) + tuple(components)

    @property
    def components(self) -> tuple[PathComponent, ...]:
        """
        Get the path components as a tuple.

        Returns:
            tuple[PathComponent, ...]: Path components including root
        """
        return self._components

    def to_tuple(self) -> tuple[PathComponent, ...]:
        """
        Get the path as a tuple for use with the backend.

        Returns:
            tuple[PathComponent, ...]: Path components as a tuple
        """
        return self._components

    def __str__(self) -> str:
        """
        Convert path to a string representation.

        Returns:
            str: Path as a string with '/' separator
        """
        if len(self._components) == 1:
            # Just the root
            return self.root_marker

        return self.root_marker + self.root_marker.join(str(comp) for comp in self._components[1:])

    def __repr__(self) -> str:
        """
        Get a detailed string representation for debugging.

        Returns:
            str: Detailed representation of the path
        """
        if len(self._components) == 1:
            return "StatePath()"

        return f"StatePath({', '.join(repr(c) for c in self._components[1:])})"

    def __eq__(self, other: object) -> bool:
        """
        Check if two paths are equal.

        Args:
            other: Another object to compare with

        Returns:
            bool: True if paths have the same components
        """
        if not isinstance(other, StatePath):
            return False
        return self._components == other._components

    def __hash__(self) -> int:
        """
        Get hash value for the path.

        Returns:
            int: Hash based on path components
        """
        return hash(self._components)

    def __len__(self) -> int:
        """
        Get the number of components in the path (including root).

        Returns:
            int: Number of components
        """
        return len(self._components)

    def __iter__(self) -> Iterator[PathComponent]:
        """
        Get an iterator over the path components.

        Returns:
            Iterator[PathComponent]: Iterator over components
        """
        return iter(self._components)

    def join(self, *components: PathComponent) -> Self:
        """
        Create a new path by joining with additional components.

        Args:
            *components: Additional components to append

        Returns:
            StatePath: New path with combined components

        Example:
            ```python
            path = StatePath("users")
            user_path = path.join("alice", "profile")
            ```
        """
        return self.__class__(*self._components[1:], *components)

    def parent(self) -> Self | None:
        """
        Get the parent path.

        Returns:
            StatePath: Parent path, or None if this is the root path

        Example:
            ```python
            path = StatePath("users", "alice")
            parent = path.parent()  # StatePath("users")
            ```
        """
        if len(self._components) <= 1:
            # This is the root path
            return None

        return self.__class__(*self._components[1:-1])

    def last(self) -> PathComponent | None:
        """
        Get the last component of the path.

        Returns:
            PathComponent: Last component

        Example:
            ```python
            path = StatePath("users", "alice")
            last = path.last()  # "alice"
            ```
        """
        if len(self._components) == 0:
            # This is the root path
            return None

        return self._components[-1]

    def is_root(self) -> bool:
        """
        Check if this is the root path.

        Returns:
            bool: True if this is the root path (only has root component)

        Example:
            ```python
            root = StatePath()
            is_root = root.is_root()  # True
            ```
        """
        return len(self._components) == 1

    @classmethod
    def from_string(cls, path_str: str) -> Self:
        """
        Create a StatePath from a string representation.

        Args:
            path_str: String representation with '/' separator

        Returns:
            StatePath: New path from the string

        Example:
            ```python
            path = StatePath.from_string("/users/alice/profile")
            ```
        """
        # Strip leading/trailing slashes, then split by slash
        clean_str = path_str.strip("/")
        if not clean_str:
            # Root path
            return cls()

        components = clean_str.split("/")
        return cls(*components)

    def is_ancestor_of(self, other: StatePath) -> bool:
        """
        Check if this path is an ancestor of another path.

        Args:
            other: Path to check against

        Returns:
            bool: True if this path is an ancestor of other

        Example:
            ```python
            users = StatePath("users")
            alice = StatePath("users", "alice")
            is_ancestor = users.is_ancestor_of(alice)  # True
            ```
        """
        if len(self._components) >= len(other._components):
            return False

        # Check if all components match up to the length of self
        return other._components[: len(self._components)] == self._components

    def is_descendant_of(self, other: StatePath) -> bool:
        """
        Check if this path is a descendant of another path.

        Args:
            other: Path to check against

        Returns:
            bool: True if this path is a descendant of other

        Example:
            ```python
            users = StatePath("users")
            alice = StatePath("users", "alice")
            is_descendant = alice.is_descendant_of(users)  # True
            ```
        """
        return other.is_ancestor_of(self)

    def relative_to(self, ancestor: StatePath) -> Self | None:
        """
        Get the relative path from an ancestor path to this path.

        Args:
            ancestor: Ancestor path

        Returns:
            StatePath: Relative path, or None if not a descendant

        Example:
            ```python
            users = StatePath("users")
            alice_profile = StatePath("users", "alice", "profile")
            relative = alice_profile.relative_to(users)  # StatePath("alice", "profile")
            ```
        """
        if not self.is_descendant_of(ancestor):
            return None

        # Get components after the ancestor
        relative_components = self._components[len(ancestor._components) :]
        return self.__class__(*relative_components)
