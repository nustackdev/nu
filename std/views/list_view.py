"""ListView - List-like view over container."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, overload

from pv.container import (
    ContainerNotFoundError,
    ContainerProtocol,
    ContainerStructure,
    NodeType,
)
from pv.typing import Empty, Value
from pv.view import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildObservableBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable

    from pv.typing.view import (
        Appendable,
        Assignable,
        ChildObservable,
        Clearable,
        Containable,
        Convertible,
        Deletable,
        Initializable,
        MutableSequenceView,
        Nestable,
        Observable,
        Sizeable,
        Subscriptable,
    )


__all__ = ["ListView", "ListSliceView"]


class ListView(
    ObservableBase,
    ChildObservableBase[int],
    MetadataBasedChildrenCountBase,
    ChildNavigationBase[int],
    ChildNestedGetBase,
    ChildNestedSetBase,
    StdView,
):
    """List-like view over container.

    Provides familiar list interface using integer keys:
    - __getitem__, __setitem__, __delitem__
    - append(), pop(), insert()
    - Index-based operations

    Type Parameters:
        V: Type of values (default: Value)

    Example:
        >>> tasks: ListView[str] = ListView(container, registry)
        >>> tasks.append("Buy groceries")
        >>> tasks.append("Write code")
        >>> print(tasks[0])  # "Buy groceries"
        >>> print(len(tasks))  # 2
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(2)
    PROTOCOL: ClassVar[ContainerProtocol] = (
        ContainerProtocol.INDEXED | ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
    )
    CONTAINER_CLS: ClassVar[type] = list

    def normalize_address(self, address: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            address: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if address < 0:
            address = length + address

        if address < 0 or address >= length:
            raise IndexError("list index out of range")

        return address

    @overload
    def __getitem__(self, address: int) -> object | Empty: ...
    @overload
    def __getitem__(self, address: slice) -> ListSliceView: ...

    def __getitem__(self, address: int | slice) -> object | Empty | ListSliceView:
        """Get item at index or slice.

        Args:
            address: Index (supports negative) or slice

        Returns:
            Value at index, or ListSliceView for slice

        Raises:
            IndexError: If index out of bounds
        """
        if isinstance(address, slice):
            return ListSliceView(self, address)

        normalized = self.normalize_address(address)
        try:
            return self._get_child_value(normalized)
        except ContainerNotFoundError as e:
            raise IndexError("list index out of bounds") from e

    def __setitem__(self, address: int, value: object) -> None:
        """Set item at index.

        Args:
            address: Index (supports negative)
            value: Value to store

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.normalize_address(address)
        self._set_child_value(normalized, value)

    def __delitem__(self, address: int) -> None:
        """Delete item at index and shift remaining items.

        Args:
            address: Index (supports negative)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.normalize_address(address)
        length = len(self)

        # Delete the item
        self.container.delete_child(normalized)

        # Shift remaining items down
        for i in range(normalized + 1, length):
            child_type = self.container.get_child_type(i)
            if child_type == NodeType.PRIMITIVE:
                value = self.container.get_child_primitive(i)
                self.container.put_child_primitive(i - 1, value)
                self.container.delete_child(i)
            elif child_type == NodeType.CONTAINER:
                # Container child - needs more complex move logic
                raise NotImplementedError(
                    "Deleting list items with container children not yet supported"
                )

        # Update length metadata
        self._set_length(length - 1)

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over items.

        Yields:
            Items in order
        """
        for k, v in self.container.iter_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield v.primitive_value
            elif v.node_type == NodeType.CONTAINER:
                yield self[int(k)]

    def __contains__(self, obj: object) -> bool:
        """Check if value exists in list.

        Args:
            obj: Value to check for

        Returns:
            True if value exists in list
        """
        for item in self:
            if item == obj:
                return True
        return False

    def append(self, value: object) -> None:
        """Append value to end.

        Args:
            value: Value to append
        """
        index = len(self)
        self._set_child_value(index, value)
        # Update length metadata
        self._set_length(index + 1)

    def pop(self, address: int = -1) -> object | Empty:
        """Remove and return item at index.

        Args:
            address: Index to remove (default: last)

        Returns:
            Removed value

        Raises:
            IndexError: If list empty or index out of bounds
        """
        if len(self) == 0:
            raise IndexError("pop from empty list")

        value = self[address]
        del self[address]
        return value

    def insert(self, address: int, value: object) -> None:
        """Insert value at index, shifting later items.

        Args:
            address: Index to insert at
            value: Value to insert
        """
        length = len(self)

        # Clamp index to valid range
        if address < 0:
            address = max(0, length + address)
        else:
            address = min(address, length)

        # Shift items up
        for i in range(length - 1, address - 1, -1):
            child_type = self.container.get_child_type(i)
            if child_type == NodeType.PRIMITIVE:
                child_value = self.container.get_child_primitive(i)
                self.container.put_child_primitive(i + 1, child_value)
            elif child_type == NodeType.CONTAINER:
                raise NotImplementedError(
                    "Inserting into list with container children not yet supported"
                )

        # Insert new value
        self._set_child_value(address, value)
        # Update length metadata
        self._set_length(length + 1)

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()
        # Reset length metadata
        self._set_length(0)

    # =========================================================================
    # FUNCTIONAL OPERATIONS
    # =========================================================================

    def map(self, fn: Callable[[object], object]) -> list[object]:
        """Apply function to each element.

        Args:
            fn: Function to apply to each element

        Returns:
            New list with transformed elements

        Example:
            >>> tasks.map(str.upper)
            >>> prices.map(lambda x: x * 2)
        """
        return [fn(item) for item in self]

    def filter(self, fn: Callable[[object], bool]) -> list[object]:
        """Filter elements by predicate.

        Args:
            fn: Predicate function - keep element if returns truthy

        Returns:
            New list with elements matching predicate

        Example:
            >>> prices.filter(lambda x: x > 100)
            >>> items.filter(bool)  # remove falsy values
        """
        return [item for item in self if fn(item)]

    def reduce(self, fn: Callable[[object, object], object], initial: object) -> object:
        """Reduce list to single value.

        Args:
            fn: Reducer function (accumulator, element) -> new_accumulator
            initial: Initial accumulator value

        Returns:
            Final accumulated value

        Example:
            >>> prices.reduce(lambda acc, x: acc + x, 0)
            >>> items.reduce(lambda acc, x: acc * x, 1)
        """
        result = initial
        for item in self:
            result = fn(result, item)
        return result

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    def index(self, value: object) -> int:
        """Find index of first occurrence of value.

        Args:
            value: Value to search for

        Returns:
            Index of first occurrence

        Raises:
            ValueError: If value not found

        Example:
            >>> items.index("apple")
        """
        for i, item in enumerate(self):
            if item == value:
                return i
        raise ValueError(f"{value!r} is not in list")

    def count(self, value: object) -> int:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Number of occurrences

        Example:
            >>> items.count("apple")
        """
        return sum(1 for item in self if item == value)

    def find(self, fn: Callable[[object], bool]) -> object:
        """Find first element matching predicate.

        Args:
            fn: Predicate function

        Returns:
            First matching element

        Raises:
            ValueError: If no element matches

        Example:
            >>> prices.find(lambda x: x > 100)
        """
        for item in self:
            if fn(item):
                return item
        raise ValueError("No matching element found")

    def find_index(self, fn: Callable[[object], bool]) -> int:
        """Find index of first element matching predicate.

        Args:
            fn: Predicate function

        Returns:
            Index of first matching element

        Raises:
            ValueError: If no element matches

        Example:
            >>> prices.find_index(lambda x: x > 100)
        """
        for i, item in enumerate(self):
            if fn(item):
                return i
        raise ValueError("No matching element found")

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> Iterable[object]:
        """Extract all items as list.

        Returns:
            List of all items in order
        """
        return list(self)

    def store(self, value: Iterable[object]) -> None:
        """Store list contents.

        Args:
            value: Sequence to store
            replace: If True, clear existing content first
        """
        self.clear()

        # Batch append and update length once at end
        count = 0
        for item in value:
            self._set_child_value(count, item)
            count += 1

        # Set final length metadata
        self._set_length(count)


class ListSliceView(ListView):
    """A view over a slice of a ListView.

    Provides a window into a portion of a list without copying data.
    Supports read operations; mutating operations raise errors.

    Example:
        >>> lst = ListView(container, registry)
        >>> lst.store([0, 1, 2, 3, 4, 5])
        >>> view = lst[1:4]  # ListSliceView over indices 1, 2, 3
        >>> print(len(view))  # 3
        >>> print(view[0])  # 1
        >>> print(list(view))  # [1, 2, 3]
    """

    _slice_start: int
    _slice_stop: int
    _slice_step: int
    _slice_length: int

    def __init__(
        self,
        parent: ListView,
        slc: slice,
    ) -> None:
        """Initialize a slice view.

        Args:
            parent: The parent ListView to slice
            slc: The slice object defining the view bounds
        """
        # Initialize with the same container and registry as parent
        super().__init__(parent.container, parent.registry)

        # Compute indices from slice using parent's length
        parent_length = len(parent)
        start, stop, step = slc.indices(parent_length)

        self._slice_start = start
        self._slice_stop = stop
        self._slice_step = step

        # Calculate slice length
        if step > 0:
            self._slice_length = max(0, (stop - start + step - 1) // step)
        else:
            self._slice_length = max(0, (stop - start + step + 1) // step)

    def __len__(self) -> int:
        """Return the length of the slice view."""
        return self._slice_length

    def _to_parent_index(self, address: int) -> int:
        """Convert a slice-relative index to a parent index.

        Args:
            address: Index relative to this slice view

        Returns:
            Absolute index in the parent list
        """
        return self._slice_start + address * self._slice_step

    def normalize_address(self, address: int) -> int:
        """Normalize index and convert to parent index.

        Args:
            address: Index relative to slice view (supports negative)

        Returns:
            Normalized absolute index in parent list

        Raises:
            IndexError: If index out of bounds
        """
        length = self._slice_length

        if address < 0:
            address = length + address

        if address < 0 or address >= length:
            raise IndexError("list index out of range")

        return self._to_parent_index(address)

    @overload
    def __getitem__(self, address: int) -> object: ...
    @overload
    def __getitem__(self, address: slice) -> ListSliceView: ...

    def __getitem__(self, address: int | slice) -> object | ListSliceView:
        """Get item at index or create sub-slice view.

        Args:
            address: Index or slice

        Returns:
            Value at index, or ListSliceView for slice

        Raises:
            IndexError: If index out of bounds
        """
        if isinstance(address, slice):
            # Create a sub-slice view
            # First, map the slice to parent indices
            start, stop, step = address.indices(self._slice_length)

            # Convert to parent coordinates
            new_start = self._to_parent_index(start)
            new_step = self._slice_step * step

            if step > 0:
                # Calculate the new stop in parent coordinates
                new_stop = (
                    self._to_parent_index(stop - 1) + self._slice_step
                    if stop > start
                    else new_start
                )
            else:
                new_stop = (
                    self._to_parent_index(stop + 1) - self._slice_step
                    if stop < start
                    else new_start
                )

            # Create a new slice view with absolute indices
            return ListSliceView._from_absolute(
                self.container, self.registry, new_start, new_stop, new_step
            )

        # Integer index
        normalized = self.normalize_address(address)
        try:
            return self._get_child_value(normalized)
        except ContainerNotFoundError as e:
            raise IndexError("list index out of bounds") from e

    @classmethod
    def _from_absolute(
        cls,
        container: object,
        registry: object,
        start: int,
        stop: int,
        step: int,
    ) -> ListSliceView:
        """Create a slice view from pre-computed absolute indices.

        Internal factory method for creating sub-slices.
        """
        # Create instance without going through __init__
        instance = object.__new__(cls)
        # Initialize base class attributes
        ListView.__init__(instance, container, registry)  # type: ignore[arg-type]
        # Set slice attributes
        instance._slice_start = start
        instance._slice_stop = stop
        instance._slice_step = step
        # Calculate length
        if step > 0:
            instance._slice_length = max(0, (stop - start + step - 1) // step)
        else:
            instance._slice_length = max(0, (stop - start + step + 1) // step)
        return instance

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over items in the slice.

        Yields:
            Items in slice order
        """
        for i in range(self._slice_length):
            parent_idx = self._to_parent_index(i)
            child_type = self.container.get_child_type(parent_idx)
            if child_type == NodeType.PRIMITIVE:
                yield self.container.get_child_primitive(parent_idx)
            elif child_type == NodeType.CONTAINER:
                yield self._get_child_value(parent_idx)

    # Mutating operations are not supported on slice views
    def __setitem__(self, address: int, value: object) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support item assignment")

    def __delitem__(self, address: int) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support item deletion")

    def append(self, value: object) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support append")

    def pop(self, address: int = -1) -> object:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support pop")

    def insert(self, address: int, value: object) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support insert")

    def clear(self) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support clear")

    def store(self, value: Iterable[object]) -> None:
        """Not supported on slice views."""
        raise TypeError("ListSliceView does not support store")


if TYPE_CHECKING:
    # Verify protocol implementations
    _subscriptable: type[Subscriptable[int, object]] = ListView
    _convertible: type[Convertible[object]] = ListView
    _initializable: type[Initializable[Iterable[object]]] = ListView
    _assignable: type[Assignable[int, object]] = ListView
    _nestable: type[Nestable[int]] = ListView
    _containable: type[Containable[object]] = ListView
    _sizeable: type[Sizeable] = ListView
    _deletable: type[Deletable[int]] = ListView
    _clearable: type[Clearable] = ListView
    _appendable: type[Appendable[object]] = ListView
    _mutable_sequence: type[MutableSequenceView[object]] = ListView
    _Observable: type[Observable] = ListView
    _Observable_children: type[ChildObservable] = ListView
