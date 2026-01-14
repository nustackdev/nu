"""DictView - Dict-like view over container for testing.

This is a minimal DictView implementation for testing the view layer.
It provides dict-like interface over Container for functional tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from everyshape.container import (
    ContainerNotFoundError,
    ContainerProtocol,
    ContainerStructure,
    NodeType,
)
from everyshape.typing import EMPTY, Empty, is_empty
from everyshape.view import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildObservableBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
    ViewBase,
)


if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping as PyMapping

    from everyshape.view import View

__all__ = [
    "DictView",
]


class DictView(
    ObservableBase,
    ChildObservableBase[str | int],
    MetadataBasedChildrenCountBase,
    ChildNavigationBase[str | int],
    ChildNestedGetBase,
    ChildNestedSetBase,
    ViewBase,
):
    """Dict-like view over container.

    Provides familiar dict interface while delegating to Container:
    - __getitem__, __setitem__, __delitem__
    - keys(), values(), items()
    - get(), pop(), clear()

    Type Parameters:
        K: Type of keys (default: str | int)
        V: Type of values

    Example:
        >>> users: DictView = DictView(container, registry)
        >>> users["alice"] = {"name": "Alice", "tags": ["python"]}
        >>> alice = users["alice"]
        >>> print(list(users.keys()))
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = dict

    @classmethod
    def get_default_parent_view(cls) -> type[View] | None:
        """Returns DictView as default parent view."""
        return cls

    @classmethod
    def get_available_views(cls) -> tuple[type[View], ...]:
        """Returns DictView as available view."""
        return (cls,)

    def normalize_address(self, address: str | int) -> str | int:
        """No normalization needed for dict keys - passthrough.

        Args:
            address: Key to access

        Returns:
            Same key unchanged
        """
        return address

    def __getitem__(self, address: str | int) -> object:
        """Get value for key.

        Args:
            address: Key to retrieve

        Returns:
            Value (auto-extracted if container)

        Raises:
            KeyError: If key not found
        """
        try:
            val = self._get_child_value(address)
        except ContainerNotFoundError as e:
            raise KeyError(address) from e

        if isinstance(val, Empty):
            raise KeyError(f"{address} not found")
        return val

    def __setitem__(self, address: str | int, value: object) -> None:
        """Set value for key.

        Args:
            address: Key to set
            value: Value to store (auto-populated if container type)
        """
        # Check if key is new before setting
        is_new = not self.container.exists_child(address)
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
        if not self.container.exists_child(address):
            raise KeyError(address)
        self.container.delete_child(address)
        # Update length metadata
        self._decrement_length()

    def __contains__(self, obj: str | int) -> bool:
        """Check if key exists.

        Args:
            obj: Key to check

        Returns:
            True if key exists
        """
        return self.container.exists_child(obj)

    def keys(self) -> Generator[str | int, None, None]:
        """Get all keys.

        Yields:
            Keys in storage order
        """
        yield from self.container.iter_child_keys()

    def values(self) -> Generator[object, None, None]:
        """Get all values.

        Yields:
            Values in storage order
        """
        for address, info in self.container.iter_children():
            if info.node_type == NodeType.PRIMITIVE:
                yield info.primitive_value
            elif info.node_type == NodeType.CONTAINER:
                yield self[address]

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        """Get all key-value pairs.

        Yields:
            (key, value) tuples in storage order
        """
        for address, info in self.container.iter_children():
            if info.node_type == NodeType.PRIMITIVE:
                yield address, info.primitive_value
            elif info.node_type == NodeType.CONTAINER:
                yield address, self[address]

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
            for address, value in other.items():
                self[address] = value
        for address, value in kwargs.items():
            self[address] = value  # type: ignore[assignment]

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> dict[str | int, object]:
        """Extract all items as dict.

        Returns:
            Dict of all key-value pairs
        """
        return dict(self.items())

    def store(self, value: PyMapping) -> None:
        """Store dict contents.

        Args:
            value: Mapping to store
        """
        self.clear()

        # Batch store and update length once at end
        count = 0
        for address, val in value.items():
            self._set_child_value(address, val)
            count += 1

        # Set final length metadata
        self._set_length(count)
