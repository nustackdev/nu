"""
Path implementation for the state management system.

This module defines the StatePath class, which represents a hierarchical path
in the state tree and provides methods for path manipulation and navigation.
"""

from __future__ import annotations

from typing import Iterator

from .._types import PathComponent

__all__ = [
    "StatePath",
]


class StatePath:
    """
    Represents a hierarchical path in the state tree.

    StatePath handles the representation and manipulation of paths for navigating
    through the state tree. It provides methods for joining paths, getting parent
    paths, and other path operations similar to filesystem paths.

    Example:
        path = StatePath("users", "alice", "profile")
        parent_path = path.parent()
        extended_path = path.join("settings")
    """

    def __init__(self, *components: PathComponent) -> None:
        """
        Initialize a path with the given components.

        Args:
            *components: Variable length argument list of path components.
                Each component should be a valid PathComponent (string).
        """
        self._components: tuple[PathComponent, ...] = tuple(*components)

    @property
    def components(self) -> tuple[PathComponent, ...]:
        """
        Get a copy of the path components.

        Returns:
            A list of path components.
        """
        return self._components

    def to_tuple(self) -> tuple[PathComponent, ...]:
        """
        Get the path as a tuple of components.

        Returns:
            A tuple of path components.
        """
        return self._components

    def __str__(self) -> str:
        """
        Convert path to a string representation.

        Returns:
            A string representation of the path using '/' as separator.
        """
        if not self._components:
            return "/"
        return "/" + "/".join(str(comp) for comp in self._components)

    def __repr__(self) -> str:
        """
        Get a detailed string representation for debugging.

        Returns:
            A detailed string representation of the path.
        """
        return f"StatePath({', '.join(repr(c) for c in self._components)})"

    def __eq__(self, other: object) -> bool:
        """
        Check if two paths are equal.

        Args:
            other: Another object to compare with.

        Returns:
            True if the paths have the same components, False otherwise.
        """
        if not isinstance(other, StatePath):
            return False
        return self._components == other._components

    def __hash__(self) -> int:
        """
        Get hash value for the path.

        Returns:
            Hash value based on the path components.
        """
        return hash(tuple(self._components))

    def __len__(self) -> int:
        """
        Get the number of components in the path.

        Returns:
            The number of components.
        """
        return len(self._components)

    def __iter__(self) -> Iterator[PathComponent]:
        """
        Get an iterator over the path components.

        Returns:
            An iterator yielding each path component.
        """
        return iter(self._components)

    def join(self, component: PathComponent, /, *components: PathComponent) -> StatePath:
        """
        Create a new path by joining with additional components.

        Args:
            *components: Additional path components to append.

        Returns:
            A new StatePath with the combined components.
        """
        return StatePath(*(self._components + tuple(component) + tuple(components)))

    def parent(self) -> "StatePath | None":
        """
        Get the parent path.

        Returns:
            The parent path, or None if this is the root path.
        """
        if not self._components:
            return None
        return StatePath(*self._components[:-1])

    def last(self) -> PathComponent | None:
        """
        Get the last component of the path.

        Returns:
            The last component, or None if the path is empty.
        """
        if not self._components:
            return None
        return self._components[-1]

    def is_root(self) -> bool:
        """
        Check if this is the root path.

        Returns:
            True if this is the root path (empty components), False otherwise.
        """
        return len(self._components) == 0

    @classmethod
    def from_string(cls, path_str: str) -> StatePath:
        """
        Create a StatePath from a string representation.

        Args:
            path_str: A string representation of a path, using '/' as separator.
                      Leading and trailing slashes are ignored.

        Returns:
            A new StatePath instance.
        """
        # Strip leading and trailing slashes, then split by slash
        parts = path_str.strip("/").split("/")
        # Filter out empty parts (happens with consecutive slashes)
        components = [part for part in parts if part]
        return cls(*components)

    def is_ancestor_of(self, other: StatePath) -> bool:
        """
        Check if this path is an ancestor of another path.

        Args:
            other: Another StatePath to check.

        Returns:
            True if this path is an ancestor of the other path, False otherwise.
        """
        if len(self) >= len(other):
            return False

        for i, comp in enumerate(self._components):
            if other._components[i] != comp:
                return False

        return True

    def is_descendant_of(self, other: StatePath) -> bool:
        """
        Check if this path is a descendant of another path.

        Args:
            other: Another StatePath to check.

        Returns:
            True if this path is a descendant of the other path, False otherwise.
        """
        return other.is_ancestor_of(self)

    def relative_to(self, ancestor: StatePath) -> "StatePath | None":
        """
        Get the relative path from an ancestor path to this path.

        Args:
            ancestor: The ancestor path.

        Returns:
            A new StatePath representing the relative path, or None if
            the given path is not an ancestor.
        """
        if not self.is_descendant_of(ancestor):
            return None

        relative_components = self._components[len(ancestor) :]
        return StatePath(*relative_components)
