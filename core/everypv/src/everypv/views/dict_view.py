"""DictView - Dict-like view over container."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, ClassVar

from pv.container import (
    ContainerNotFoundError,
    ContainerProtocol,
    ContainerStructure,
    NodeType,
)
from pv.types import EMPTY, Empty, is_empty
from pv.view import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildObservableBase,
    ChildPrimitiveSetBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
    UnsafePrimitiveOpsBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from collections.abc import Mapping as PyMapping

    from pv.collections import MutableMappingView
    from pv.traits import (
        Assignable,
        ChildObservable,
        Clearable,
        Containable,
        Convertible,
        Deletable,
        Initializable,
        Nestable,
        Observable,
        Sizeable,
        Subscriptable,
    )

__all__ = [
    "DictISliceView",
    "DictView",
]


class DictView(
    ObservableBase,
    ChildObservableBase[str | int],
    MetadataBasedChildrenCountBase,
    ChildNavigationBase[str | int],
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
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

    @classmethod
    def is_address_static(cls, address: object) -> bool:
        """Dict keys are always passthrough — no normalization needed."""
        return True

    def normalize_address(self, address: str | int) -> str | int:
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
        except ContainerNotFoundError as e:
            raise KeyError(address) from e

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
        self.ensure_created()
        self.container.delete_child(address)
        # Update length metadata
        self._update_count()

    def __contains__(self, obj: str | int) -> bool:
        """Check if key exists.

        Args:
            obj: Key to check

        Returns:
            True if key exists
        """
        return self.container.exists_child(obj)

    def __iter__(self) -> Generator[str | int, None, None]:
        """Iterate over keys."""
        yield from self.keys()

    def keys(self) -> Generator[str | int, None, None]:
        """Get all keys.

        Yields:
            Keys in storage order
        """
        yield from self.container.iter_child_keys(validate=False)

    def values(self) -> Generator[object, None, None]:
        """Get all values.

        Yields:
            Values in storage order
        """
        for k, v in self.container.iter_children(validate=False):
            if v.node_type == NodeType.PRIMITIVE:
                yield v.primitive_value
            elif v.node_type == NodeType.CONTAINER:
                # Pass node_info to avoid redundant read
                yield self._get_child_value(k, node_info=v)

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        """Get all key-value pairs.

        Yields:
            (key, value) tuples in storage order
        """
        for k, v in self.container.iter_children(validate=False):
            if v.node_type == NodeType.PRIMITIVE:
                yield k, v.primitive_value
            elif v.node_type == NodeType.CONTAINER:
                # Pass node_info to avoid redundant read
                yield k, self._get_child_value(k, node_info=v)

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
        self.ensure_created()
        self.container.clear_children(validate=True)
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

    # =========================================================================
    # FUNCTIONAL OPERATIONS
    # =========================================================================

    def map_values(self, fn: Callable[[object], object]) -> dict[str | int, object]:
        """Apply function to each value, keeping keys unchanged.

        Args:
            fn: Function to apply to each value

        Returns:
            New dict with transformed values

        Example:
            >>> users.map_values(str.upper)
            >>> prices.map_values(lambda x: x * 2)
        """
        return {k: fn(v) for k, v in self.items()}

    def map_items(
        self, fn: Callable[[str | int, object], tuple[str | int, object]]
    ) -> dict[str | int, object]:
        """Apply function to each (key, value) pair.

        Args:
            fn: Function that takes (key, value) and returns new (key, value)

        Returns:
            New dict with transformed items

        Example:
            >>> data.map_items(lambda k, v: (k.upper(), v * 2))
        """
        return dict(fn(k, v) for k, v in self.items())

    def filter(self, fn: Callable[[str | int, object], bool]) -> dict[str | int, object]:
        """Filter items by predicate.

        Args:
            fn: Predicate function (key, value) -> bool

        Returns:
            New dict with items matching predicate

        Example:
            >>> prices.filter(lambda k, v: v > 100)
            >>> users.filter(lambda k, v: k.startswith("a"))
        """
        return {k: v for k, v in self.items() if fn(k, v)}

    def reduce(self, fn: Callable[[object, str | int, object], object], initial: object) -> object:
        """Reduce dict to single value.

        Args:
            fn: Reducer function (accumulator, key, value) -> new_accumulator
            initial: Initial accumulator value

        Returns:
            Final accumulated value

        Example:
            >>> prices.reduce(lambda acc, k, v: acc + v, 0)  # sum values
            >>> data.reduce(lambda acc, k, v: {**acc, k: v * 2}, {})
        """
        result = initial
        for k, v in self.items():
            result = fn(result, k, v)
        return result

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    def find(self, fn: Callable[[object], bool]) -> object:
        """Find first value matching predicate.

        Args:
            fn: Predicate function applied to values

        Returns:
            First matching value

        Raises:
            ValueError: If no value matches

        Example:
            >>> prices.find(lambda v: v > 100)
        """
        for v in self.values():
            if fn(v):
                return v
        raise ValueError("No matching value found")

    def find_key(self, fn: Callable[[object], bool]) -> str | int:
        """Find first key whose value matches predicate.

        Args:
            fn: Predicate function applied to values

        Returns:
            Key of first matching value

        Raises:
            ValueError: If no value matches

        Example:
            >>> prices.find_key(lambda v: v > 100)
        """
        for k, v in self.items():
            if fn(v):
                return k
        raise ValueError("No matching value found")

    def find_item(self, fn: Callable[[str | int, object], bool]) -> tuple[str | int, object]:
        """Find first item (key, value) matching predicate.

        Args:
            fn: Predicate function (key, value) -> bool

        Returns:
            First matching (key, value) tuple

        Raises:
            ValueError: If no item matches

        Example:
            >>> data.find_item(lambda k, v: k.startswith("user") and v > 0)
        """
        for k, v in self.items():
            if fn(k, v):
                return k, v
        raise ValueError("No matching item found")

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> dict[str | int, object]:
        """Extract all items as dict.

        Returns:
            Dict of all key-value pairs
        """
        return dict(self.items())

    def store(self, value: PyMapping[str | int, object], *, replace: bool = True) -> None:
        """Store dict contents.

        Args:
            value: Mapping to store
            replace: If True, clear existing content first (default True)
        """
        self.ensure_created()
        # Optimization: only clear if container has children
        if replace:
            current_len = len(self)
            if current_len > 0:
                self.clear()

        # Batch store and update length once at end
        count = 0
        for key, val in value.items():
            self._set_child_value(key, val)
            count += 1

        # Set final length metadata
        self._set_length(count)


class DictISliceView:
    """A view over a slice of a DictView using itertools.islice semantics.

    Provides a read-only window into a portion of a dict based on iteration order.
    Unlike list slices, dict islice works on iteration order of keys.

    Example:
        >>> dct = DictView(container, registry)
        >>> dct.store({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
        >>> view = DictISliceView(dct, 1, 4)  # keys b, c, d
        >>> print(len(view))  # 3
        >>> print(list(view.keys()))  # ["b", "c", "d"]
    """

    _parent: DictView
    _start: int
    _stop: int | None
    _cached_keys: list[str | int] | None

    def __init__(
        self,
        parent: DictView,
        start: int = 0,
        stop: int | None = None,
    ) -> None:
        """Initialize an islice view.

        Args:
            parent: The parent DictView to slice
            start: Start index in iteration order
            stop: Stop index in iteration order (None for end)
        """
        self._parent = parent
        self._start = start
        self._stop = stop
        self._cached_keys = None

    def _get_sliced_keys(self) -> list[str | int]:
        """Get the keys in the slice range."""
        if self._cached_keys is None:
            all_keys = list(self._parent.keys())
            self._cached_keys = all_keys[self._start : self._stop]
        return self._cached_keys

    def __len__(self) -> int:
        """Return the length of the slice view."""
        return len(self._get_sliced_keys())

    def __getitem__(self, key: str | int) -> object | Empty:
        """Get value for key if in slice range."""
        if key in self._get_sliced_keys():
            return self._parent[key]
        raise KeyError(key)

    def __contains__(self, key: str | int) -> bool:
        """Check if key is in the slice range."""
        return key in self._get_sliced_keys()

    def keys(self) -> Generator[str | int, None, None]:
        """Get keys in the slice range."""
        yield from self._get_sliced_keys()

    def values(self) -> Generator[object, None, None]:
        """Get values in the slice range."""
        for k in self._get_sliced_keys():
            yield self._parent[k]

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        """Get key-value pairs in the slice range."""
        for k in self._get_sliced_keys():
            yield k, self._parent[k]

    def extract(self) -> dict[str | int, object]:
        """Extract slice as dict."""
        return {k: self._parent[k] for k in self._get_sliced_keys()}


MutableMapping.register(DictView)


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
    _mutable_mapping: type[MutableMappingView[str | int, object]] = DictView
    _Observable: type[Observable] = DictView
    _Observable_children: type[ChildObservable] = DictView
