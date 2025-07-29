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

    def evaluate(self, tree: "Tree", ctx: Any = None) -> Any:
        """
        This method is an alias for resolve() to maintain compatibility
        with Query evaluation patterns.

        Args:
            tree: Tree instance to evaluate path against
            ctx: Optional context for evaluation

        Returns:
            Value at the path location in the tree
        """
        return self.resolve(tree, ctx)

    # =========================================================================
    # QUERY INTEGRATION
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

    # =========================================================================
    # QUERY CHAINING INTEGRATION
    # =========================================================================

    # =========================================================================
    # ARITHMETIC OPERATIONS (Query Chaining)
    # =========================================================================

    def __add__(self, other: Any) -> "Query":
        """
        Add string or Query to path, returning a new Query.

        This allows chaining operations directly on the path.

        Args:
            other: String to append or another Query

        Returns:
            New Query with the path and additional operation

        Example:
            ```python
            path = tree.P.users.alice.email
            query = path + "hello" + "world"
            ```
        """
        return self.to_query() + other

    def __sub__(self, other: Any) -> "Query":
        """
        Subtraction: path - other

        Args:
            other: Value to subtract

        Returns:
            New Query with subtraction operation
        """
        return self.to_query() - other

    def __mul__(self, other: Any) -> "Query":
        """
        Multiplication: path * other

        Args:
            other: Value to multiply by

        Returns:
            New Query with multiplication operation
        """
        return self.to_query() * other

    def __truediv__(self, other: Any) -> "Query":
        """
        Division: path / other

        Args:
            other: Value to divide by

        Returns:
            New Query with division operation
        """
        return self.to_query() / other

    def __mod__(self, other: Any) -> "Query":
        """
        Modulo: path % other

        Args:
            other: Value to get modulo with

        Returns:
            New Query with modulo operation
        """
        return self.to_query() % other

    def __pow__(self, other: Any) -> "Query":
        """
        Power: path ** other

        Args:
            other: Exponent value

        Returns:
            New Query with power operation
        """
        return self.to_query() ** other

    def __abs__(self) -> "Query":
        """
        Absolute value: abs(path)

        Returns:
            New Query with abs operation
        """
        return abs(self.to_query())

    # =========================================================================
    # COMPARISON OPERATIONS (Query Chaining)
    # =========================================================================

    def __gt__(self, other: Any) -> "Query":
        """
        Greater than: path > other

        Args:
            other: Value to compare against

        Returns:
            New Query with greater than operation
        """
        return self.to_query() > other

    def __lt__(self, other: Any) -> "Query":
        """
        Less than: path < other

        Args:
            other: Value to compare against

        Returns:
            New Query with less than operation
        """
        return self.to_query() < other

    def __ge__(self, other: Any) -> "Query":
        """
        Greater than or equal: path >= other

        Args:
            other: Value to compare against

        Returns:
            New Query with greater than or equal operation
        """
        return self.to_query() >= other

    def __le__(self, other: Any) -> "Query":
        """
        Less than or equal: path <= other

        Args:
            other: Value to compare against

        Returns:
            New Query with less than or equal operation
        """
        return self.to_query() <= other

    def __eq__(self, other: Any) -> "Query":
        """
        Equality: path == other

        Args:
            other: Value to compare against

        Returns:
            New Query with equality operation

        Note:
            This overrides object equality for query chaining.
            Use is_equal_path() for Path comparison if needed.
        """
        return self.to_query() == other

    def __ne__(self, other: Any) -> "Query":
        """
        Not equal: path != other

        Args:
            other: Value to compare against

        Returns:
            New Query with not equal operation
        """
        return self.to_query() != other

    # =========================================================================
    # LOGICAL OPERATIONS (Query Chaining)
    # =========================================================================

    def and_(self, other: Any) -> "Query":
        """
        Logical AND: path.and_(other)

        Args:
            other: Value to AND with (can be another Query or Path)

        Returns:
            New Query with AND operation
        """
        return self.to_query().and_(other)

    def or_(self, other: Any) -> "Query":
        """
        Logical OR: path.or_(other)

        Args:
            other: Value to OR with (can be another Query or Path)

        Returns:
            New Query with OR operation
        """
        return self.to_query().or_(other)

    def __invert__(self) -> "Query":
        """
        Logical NOT: ~path or not path

        Returns:
            New Query with NOT operation
        """
        return ~self.to_query()

    # =========================================================================
    # STRING OPERATIONS (Query Chaining)
    # =========================================================================

    def contains(self, item: Any) -> "Query":
        """
        Contains check: path.contains(item)

        Args:
            item: Item to check for containment

        Returns:
            New Query with contains operation
        """
        return self.to_query().contains(item)

    def startswith(self, prefix: str) -> "Query":
        """
        String starts with: path.startswith(prefix)

        Args:
            prefix: Prefix to check for

        Returns:
            New Query with startswith operation
        """
        return self.to_query().startswith(prefix)

    def endswith(self, suffix: str) -> "Query":
        """
        String ends with: path.endswith(suffix)

        Args:
            suffix: Suffix to check for

        Returns:
            New Query with endswith operation
        """
        return self.to_query().endswith(suffix)

    # =========================================================================
    # FUNCTION OPERATIONS (Query Chaining)
    # =========================================================================

    def length(self) -> "Query":
        """
        Length: path.length()

        Returns:
            New Query with length operation
        """
        return self.to_query().length()

    def max(self) -> "Query":
        """
        Maximum: path.max()

        Returns:
            New Query with max operation
        """
        return self.to_query().max()

    def min(self) -> "Query":
        """
        Minimum: path.min()

        Returns:
            New Query with min operation
        """
        return self.to_query().min()

    def sum(self) -> "Query":
        """
        Sum: path.sum()

        Returns:
            New Query with sum operation
        """
        return self.to_query().sum()

    def any(self) -> "Query":
        """
        Any: path.any() - returns True if any element is truthy

        Returns:
            New Query with any operation
        """
        return self.to_query().any()

    def every(self) -> "Query":
        """
        Every: path.every() - returns True if all elements are truthy

        Returns:
            New Query with every operation
        """
        return self.to_query().every()

    def all(self) -> "Query":
        """
        All: path.all() - alias for every()

        Returns:
            New Query with every operation
        """
        return self.to_query().all()

    def count(self) -> "Query":
        """
        Count: path.count() - count non-None values

        Returns:
            New Query with count operation
        """
        return self.to_query().count()

    def bool(self) -> "Query":
        """
        Boolean conversion: path.bool()

        Returns:
            New Query with bool operation
        """
        return self.to_query().bool()
