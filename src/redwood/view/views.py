"""Built-in views."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from redwood.abc import EMPTY, Empty, KeyComponent, Value, is_empty
from redwood.tree import (
    Container,
    ContainerProtocol,
    ContainerStructure,
    NodeType,
    PathNotFoundError,
    join_component,
)

from .view import View


if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

# =============================================================================
# DICTVIEW
# =============================================================================


class DictView(View):
    """Dict-like view over container.

    Provides familiar dict interface while delegating to Container:
    - __getitem__, __setitem__, __delitem__
    - keys(), values(), items()
    - get(), pop(), clear()

    Example:
        >>> users = DictView(container, registry)
        >>> users["alice"] = {"name": "Alice", "tags": ["python"]}
        >>> alice = users["alice"]
        >>> print(list(users.keys()))
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = dict

    def __getitem__(self, key: KeyComponent) -> Value | Empty:
        """Get value for key.

        Args:
            key: Key to retrieve

        Returns:
            Value (auto-extracted if container)

        Raises:
            KeyError: If key not found
        """
        try:
            return self._get_child_value(key)
        except PathNotFoundError as e:
            raise KeyError(key) from e

    def __setitem__(self, key: KeyComponent, value: Value) -> None:
        """Set value for key.

        Args:
            key: Key to set
            value: Value to store (auto-populated if container type)
        """
        self._set_child_value(key, value)

    def __delitem__(self, key: KeyComponent) -> None:
        """Delete key.

        Args:
            key: Key to delete

        Raises:
            KeyError: If key not found
        """
        deleted = self.container.delete_child(key)
        if not deleted:
            raise KeyError(key)

    def __contains__(self, key: KeyComponent) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of keys.

        Returns:
            Number of keys
        """
        return self.container.count_children()

    def keys(self) -> Generator[KeyComponent, None, None]:
        """Get all keys.

        Yields:
            Keys in storage order
        """
        yield from self.container.list_child_keys()

    def values(self) -> Generator[Value, None, None]:
        """Get all values.

        Yields:
            Values in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield cast("Value", v.primitive_value)
            elif v.node_type == NodeType.CONTAINER:
                yield cast("Value", self[k])

    def items(self) -> Generator[tuple[KeyComponent, Value], None, None]:
        """Get all key-value pairs.

        Yields:
            (key, value) tuples in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield k, cast("Value", v.primitive_value)
            elif v.node_type == NodeType.CONTAINER:
                yield k, cast("Value", self[k])

    def get(self, key: KeyComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """Get value with default fallback.

        Args:
            key: Key to retrieve
            default: Default if key not found

        Returns:
            Value or default
        """
        try:
            return self._get_child_value(key)
        except Exception:
            return default

    def pop(self, key: KeyComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """Remove and return value.

        Args:
            key: Key to remove
            default: Default if key not found

        Returns:
            Removed value or default

        Raises:
            KeyError: If key not found and no default
        """
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if is_empty(default):
                raise
            return default

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()

    def update(self, other: Mapping[KeyComponent, Value] | None = None, **kwargs: Value) -> None:
        """Update from dict or kwargs.

        Args:
            other: Dict to update from
            **kwargs: Additional key-value pairs
        """
        if other:
            for key, value in other.items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def extract(self, *args: object, **kwargs: object) -> dict[KeyComponent, Value]:
        """Extract all items as dict.

        Returns:
            Dict of all key-value pairs
        """
        return dict(self.items())

    def store(
        self, value: Mapping, /, *args: object, replace: bool = False, **kwargs: object
    ) -> None:
        """Store dict contents."""
        if replace:
            self.clear()

        for key, val in value.items():
            self[key] = val

    def open_view[ViewT: View](self, key: KeyComponent, child_view: type[ViewT]) -> ViewT:
        """Open child view."""
        child_container = Container(self.container.ctx, join_component(self.container.path, key))
        return child_view(child_container, self.registry)
