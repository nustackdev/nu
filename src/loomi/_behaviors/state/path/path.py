"""
Path implementation for tree navigation.

This module provides the Path class for pure path construction and evaluation.
Paths are immutable objects that represent navigation through the tree structure
without any query operations or logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

import attrs

from .exceptions import PathConstructionError
from .types import PathComponent

if TYPE_CHECKING:
    from ..query import Query
    from ..tree import Tree

__all__ = [
    "Path",
]


@attrs.define(frozen=True, slots=True)
class Path:
    """
    Pure path construction and evaluation - no query knowledge.

    Paths represent navigation through the tree structure using attribute access
    and indexing. They are immutable and can be evaluated against tree data
    to retrieve actual values.

    Example:
        ```python
        # Path construction
        path = tree.P.users.alice.profile["email"]

        # Path evaluation
        email = path.evaluate()

        # Paths are immutable - operations return new paths
        age_path = tree.P.users.alice.age
        profile_path = age_path.parent().profile  # Navigate back and down
        ```
    """

    components: tuple[PathComponent, ...] = attrs.field(factory=tuple)

    # =========================================================================
    # PATH CONSTRUCTION (Navigation Methods)
    # =========================================================================

    def __getattr__(self, name: str) -> Path:
        """
        Navigate to attribute: path.users → new Path

        Args:
            name: Attribute name to navigate to

        Returns:
            New Path with extended components

        Raises:
            PathConstructionError: If attribute name is invalid

        Example:
            ```python
            users_path = tree.P.users
            alice_path = users_path.alice
            ```
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if not isinstance(name, str) or not name.isidentifier():
            raise PathConstructionError(f"Invalid attribute name: {name}")

        return Path(tuple(self.components) + (name,))

    def __getitem__(self, key: Union[int, str]) -> Path:
        """
        Navigate by index/key: path[0] or path["key"] → new Path

        Args:
            key: Index (int) or key (str) to navigate to

        Returns:
            New Path with extended components

        Raises:
            PathConstructionError: If key type is invalid

        Example:
            ```python
            first_user = tree.P.users[0]
            user_by_name = tree.P.users["alice"]
            last_item = tree.P.items[-1]
            ```
        """
        if not isinstance(key, (int, str)):
            raise PathConstructionError(f"Invalid key type: {type(key)}. Must be int or str")

        return Path(tuple(self.components) + (key,))

    # =========================================================================
    # PATH MANIPULATION
    # =========================================================================

    def join(self, *components: PathComponent) -> Path:
        """
        Join additional components to create new path.

        Args:
            *components: Components to append to path

        Returns:
            New Path with combined components

        Example:
            ```python
            base = tree.P.users
            alice_email = base.join("alice", "profile", "email")
            ```
        """
        return Path(tuple(self.components) + tuple(components))

    def parent(self) -> Path | None:
        """
        Get parent path.

        Returns:
            New Path for parent, or None if already at root

        Example:
            ```python
            email_path = tree.P.users.alice.email
            alice_path = email_path.parent()  # tree.P.users.alice
            users_path = alice_path.parent()  # tree.P.users
            root_path = users_path.parent()   # tree.P
            none_path = root_path.parent()    # None
            ```
        """
        if not self.components:
            return None

        return Path(tuple(self.components[:-1]))

    def last_component(self) -> PathComponent | None:
        """
        Get the last component of the path.

        Returns:
            Last component or None if path is root

        Example:
            ```python
            path = tree.P.users.alice.email
            last = path.last_component()  # "email"
            ```
        """
        return self.components[-1] if self.components else None

    def is_root(self) -> bool:
        """
        Check if this is the root path.

        Returns:
            True if path has no components

        Example:
            ```python
            root = tree.P
            assert root.is_root() == True

            users = tree.P.users
            assert users.is_root() == False
            ```
        """
        return len(self.components) == 0

    def is_ancestor_of(self, other: Path) -> bool:
        """
        Check if this path is an ancestor of another path.

        Args:
            other: Path to check against

        Returns:
            True if this path is an ancestor of other

        Example:
            ```python
            users = tree.P.users
            alice = tree.P.users.alice
            email = tree.P.users.alice.email

            assert users.is_ancestor_of(alice) == True
            assert users.is_ancestor_of(email) == True
            assert alice.is_ancestor_of(email) == True
            assert email.is_ancestor_of(alice) == False
            ```
        """
        if not isinstance(other, Path):
            return False

        if len(self.components) >= len(other.components):
            return False

        return other.components[: len(self.components)] == self.components

    def is_descendant_of(self, other: Path) -> bool:
        """
        Check if this path is a descendant of another path.

        Args:
            other: Path to check against

        Returns:
            True if this path is a descendant of other

        Example:
            ```python
            users = tree.P.users
            alice = tree.P.users.alice

            assert alice.is_descendant_of(users) == True
            assert users.is_descendant_of(alice) == False
            ```
        """
        return other.is_ancestor_of(self)

    def relative_to(self, ancestor: Path) -> Path | None:
        """
        Get relative path from ancestor to this path.

        Args:
            ancestor: Ancestor path

        Returns:
            Relative path or None if not a descendant

        Example:
            ```python
            users = tree.P.users
            email = tree.P.users.alice.profile.email

            relative = email.relative_to(users)  # Path equivalent to P.alice.profile.email
            ```
        """
        if not self.is_descendant_of(ancestor):
            return None

        relative_components = self.components[len(ancestor.components) :]
        return Path(relative_components)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def __str__(self) -> str:
        """
        String representation for display.

        Returns:
            Human-readable path string

        Example:
            ```python
            path = tree.P.users.alice.email
            str(path)  # "P.users.alice.email"
            ```
        """
        if not self.components:
            return "P"
        return "P." + ".".join(str(c) for c in self.components)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            Detailed representation showing components

        Example:
            ```python
            path = tree.P.users.alice.email
            repr(path)  # "Path(['users', 'alice', 'email'])"
            ```
        """
        return f"Path({list(self.components)})"

    def __hash__(self) -> int:
        """
        Hash value for path (enables use in sets/dicts).

        Returns:
            Hash based on components and tree reference
        """
        return hash((self.components))

    # =========================================================================
    # PATH RESOLUTION
    # =========================================================================

    def resolve(self, tree: "Tree", ctx: Any = None) -> Any:
        """
        Resolve path to its value in the tree.

        This method uses the PathResolver to navigate through the tree
        structure and retrieve the actual value at the specified path.
        It serves as the bridge between the path and tree data.

        Args:
            tree: Tree instance to resolve path against
            ctx: Optional context for path resolution

        Returns:
            Value at the path location in the tree

        Raises:
            PathNotFoundError: If path cannot be resolved
            PathEvaluationError: If resolution fails

        Example:
            ```python
            # Resolve path to actual value
            email = path.resolve(tree)

            # Resolve with transaction context
            with tree.transaction() as tx:
                value = path.resolve(tree, ctx=tx)
            ```
        """
        from ..path.resolver import PathResolver

        return PathResolver().resolve(self, tree, ctx)

    # =========================================================================
    # QUERY INTERFACE
    # =========================================================================

    def to_query(self) -> "Query":
        """
        Convert path to a Query object.

        This allows using the path in query operations while maintaining
        the pure path semantics.

        Returns:
            Query object representing this path

        Example:
            ```python
            path = tree.P.users.alice.email
            query = path.to_query()
            # Now can use query operations on this path
            ```
        """
        from ..query import Query

        return Query.create(self)

    def Q(self) -> "Query":
        """
        Alias for to_query() method.

        Provides a more concise way to convert path to Query.

        Returns:
            Query object representing this path

        Example:
            ```python
            path = tree.P.users.alice.email
            query = path.Q()
            ```
        """
        return self.to_query()
