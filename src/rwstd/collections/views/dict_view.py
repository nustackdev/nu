"""DictView - Dict-like view over container."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from redwood.tree import (
    ContainerProtocol,
    ContainerStructure,
    NodeType,
    PathNotFoundError,
)
from redwood.types import EMPTY, Empty, cast_value, is_empty
from redwood.view import (
    ChildNavigationMixin,
    ChildNestedGetMixin,
    ChildNestedSetMixin,
    MetadataBasedChildrenCountMixin,
    WatchMixin,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping as PyMapping

    from redwood.types import (
        Assignable,
        Clearable,
        Containable,
        Convertible,
        Deletable,
        Initializable,
        MutableMapping,
        Nestable,
        Sizeable,
        Subscriptable,
    )

__all__ = [
    "DictView",
]


class DictView(
    WatchMixin[str | int],
    MetadataBasedChildrenCountMixin,
    ChildNavigationMixin[str | int],
    ChildNestedGetMixin,
    ChildNestedSetMixin,
    StdView,
):
    """Dict-like view over container.

    Provides familiar dict interface while delegating to Container:
    - __getitem__, __setitem__, __delitem__
    - keys(), values(), items()
    - get(), pop(), clear()

    Type Parameters:
        K: Type of keys (default: str | int, constrained to str or int)
        V: Type of values (default: Value)

    Example:
        >>> users: DictView[str, dict] = DictView(container, registry)
        >>> users["alice"] = {"name": "Alice", "tags": ["python"]}
        >>> alice = users["alice"]
        >>> print(list(users.keys()))
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = dict

    def address_normalization(self, address: str | int) -> str | int:
        """No normalization needed for dict keys - passthrough.

        Args:
            address: Key to access

        Returns:
            Same key unchanged
        """
        return address

    def __getitem__(self, address: str | int) -> object | Empty:
        """Get value for key.

        Args:
            address: Key to retrieve

        Returns:
            Value (auto-extracted if container)

        Raises:
            KeyError: If key not found
        """
        try:
            return self._get_child_value(address)
        except PathNotFoundError as e:
            raise KeyError(address) from e

    def __setitem__(self, address: str | int, value: object) -> None:
        """Set value for key.

        Args:
            address: Key to set
            value: Value to store (auto-populated if container type)
        """
        # Check if key is new before setting
        is_new = not self.container.has_child(address)
        self._set_child_value(address, value)
        # Update length metadata if new key
        if is_new:
            self._increment_length()

    def __delitem__(self, address: str | int) -> None:
        """Delete key.

        Args:
            address: Key to delete

        Raises:
            KeyError: If key not found
        """
        deleted = self.container.delete_child(address)
        if not deleted:
            raise KeyError(address)
        # Update length metadata
        self._decrement_length()

    def __contains__(self, obj: str | int) -> bool:
        """Check if key exists.

        Args:
            obj: Key to check

        Returns:
            True if key exists
        """
        return self.container.has_child(obj)

    def keys(self) -> Generator[str | int, None, None]:
        """Get all keys.

        Yields:
            Keys in storage order
        """
        yield from self.container.list_child_keys()

    def values(self) -> Generator[object, None, None]:
        """Get all values.

        Yields:
            Values in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield cast_value(v.primitive_value)  # type: ignore[misc]
            elif v.node_type == NodeType.CONTAINER:
                yield cast_value(self[k])  # type: ignore[misc]

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        """Get all key-value pairs.

        Yields:
            (key, value) tuples in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield k, cast_value(v.primitive_value)  # type: ignore[misc]
            elif v.node_type == NodeType.CONTAINER:
                yield k, cast_value(self[k])  # type: ignore[misc]

    def get(self, address: str | int, default: object | Empty = EMPTY) -> object | Empty:
        """Get value with default fallback.

        Args:
            address: Key to retrieve
            default: Default if key not found

        Returns:
            Value or default
        """
        try:
            return self._get_child_value(address)
        except Exception:
            return default

    def pop(self, address: str | int, default: object | Empty = EMPTY) -> object | Empty:
        """Remove and return value.

        Args:
            address: Key to remove
            default: Default if key not found

        Returns:
            Removed value or default

        Raises:
            KeyError: If key not found and no default
        """
        try:
            value = self[address]
            del self[address]
            return value
        except KeyError:
            if is_empty(default):
                raise
            return default

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()
        # Reset length metadata
        self._set_length(0)

    def update(self, other: PyMapping[str | int, object] | None = None, **kwargs: object) -> None:
        """Update from dict or kwargs.

        Args:
            other: Dict to update from
            **kwargs: Additional key-value pairs
        """
        if other:
            for key, value in other.items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value  # type: ignore[assignment]

    def extract(self) -> dict[str | int, object]:
        """Extract all items as dict.

        Returns:
            Dict of all key-value pairs
        """
        return dict(self.items())

    def store(self, value: PyMapping[str | int, object]) -> None:
        """Store dict contents.

        Args:
            value: Mapping to store
            replace: If True, clear existing content first
        """
        self.clear()

        # Batch store and update length once at end
        count = 0
        for key, val in value.items():
            self._set_child_value(key, val)
            count += 1

        # Set final length metadata
        self._set_length(count)


if TYPE_CHECKING:
    # Verify protocol implementations
    _subscriptable: type[Subscriptable[str | int, object]] = DictView
    _convertible: type[Convertible[object]] = DictView
    _initializable: type[Initializable[PyMapping[str | int, object]]] = DictView
    _assignable: type[Assignable[str | int, object]] = DictView
    _nestable: type[Nestable[str | int]] = DictView
    _containable: type[Containable[str | int]] = DictView
    _sizeable: type[Sizeable] = DictView
    _deletable: type[Deletable[str | int]] = DictView
    _clearable: type[Clearable] = DictView
    _mutable_mapping: type[MutableMapping[str | int, object]] = DictView
