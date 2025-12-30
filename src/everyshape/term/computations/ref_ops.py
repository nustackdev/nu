"""Concrete operation classes for LValue references.

This module provides concrete operations for refs that work uniformly
across all ref types. Operations are pure computations that read data.

Operations (pure computations):
    - GetOp: Read primitive value from ref
    - ExtractOp: Read entire container structure
    - ExistsOp: Check if location exists
    - MissingOp: Check if location is missing
    - LengthOp: Get container length

Sequence Operations:
    - MapOp: Map function over sequence
    - FilterOp: Filter sequence by predicate
    - ReduceOp: Reduce sequence to single value
    - IndexOp: Find index of value
    - CountOp: Count occurrences
    - FindOp: Find first matching element
    - FindIndexOp: Find index of first match

Mapping Operations:
    - KeysOp: Get all keys
    - ValuesOp: Get all values
    - ItemsOp: Get all key-value pairs
    - MapValuesOp: Map function over values
    - MapItemsOp: Map function over items
    - FilterItemsOp: Filter items by predicate
    - ReduceItemsOp: Reduce items to single value
    - FindKeyOp: Find key by value predicate
    - FindValueOp: Find value by predicate
    - FindItemOp: Find item by predicate
"""

from __future__ import annotations

from functools import reduce as functools_reduce
from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.term.term import Operation, PrimitiveRef, ViewRef
from everyshape.types import Empty, SpecialValue, Value
from everyshape.view import capabilities as view_capabilities


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.view import View

    from ..context import Context
    from ..refs import UnionRefBases


__all__ = [  # noqa: RUF022
    # Core operations
    "GetOp",
    "ExtractOp",
    "ExistsOp",
    "MissingOp",
    "LengthOp",
    # Sequence operations
    "MapOp",
    "FilterOp",
    "ReduceOp",
    "IndexOp",
    "CountOp",
    "FindOp",
    "FindIndexOp",
    # Mapping operations
    "KeysOp",
    "ValuesOp",
    "ItemsOp",
    "MapValuesOp",
    "MapItemsOp",
    "FilterItemsOp",
    "ReduceItemsOp",
    "FindKeyOp",
    "FindValueOp",
    "FindItemOp",
]


# =============================================================================
# CORE OPERATIONS
# =============================================================================


class GetOp[T](Operation[T | SpecialValue]):
    """Read operation for primitive values.

    Pure operation that navigates to a location and reads the value.
    Returns Empty if the value doesn't exist.

    Type Parameters:
        T: Type of value to read
        ContextT: Execution context type

    Example:
        >>> get_op = GetOp(value_ref)
        >>> value = get_op.execute(ctx)  # Returns T | SpecialValue
    """

    def __init__(self, ref: PrimitiveRef[T] | UnionRefBases) -> None:
        """Initialize get operation.

        Args:
            ref: Reference to read from
        """
        self.ref = cast("PrimitiveRef", ref)
        self.children = (cast("PrimitiveRef", ref),)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute read operation.

        Args:
            context: Execution context

        Returns:
            Value read from storage, or Empty if not found
        """
        # Resolve ref to path
        value_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to parent and get key
        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_capabilities.Subscriptable):
                return parent_view[key]
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"GetOp({self.ref!r})"


class ExtractOp[T](Operation[T | SpecialValue]):
    """Extract operation for container structures.

    Pure operation that reads an entire container structure.
    Returns the extracted data as dict/list/etc.

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)
        ContextT: Execution context type

    Example:
        >>> extract_op = ExtractOp(view_ref)
        >>> data = extract_op.execute(ctx)  # Returns dict/list/etc
    """

    def __init__(self, ref: ViewRef[view_capabilities.Convertible[T]] | UnionRefBases) -> None:
        """Initialize extract operation.

        Args:
            ref: View reference to extract from
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[T]]", ref)
        self.children = (cast("ViewRef[view_capabilities.Convertible[T]]", ref),)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute extract operation.

        Args:
            context: Execution context

        Returns:
            Extracted data, or Empty if not found
        """
        # Resolve ref to path
        view_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to view
        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                return view.extract()

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ExtractOp({self.ref!r})"


class ExistsOp(Operation[bool]):
    """Existence check operation.

    Pure operation that checks if a location exists in storage.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> exists_op = ExistsOp(ref)
        >>> exists = exists_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PrimitiveRef[Value] | ViewRef[View] | UnionRefBases) -> None:
        """Initialize exists operation.

        Args:
            ref: Reference to check
        """
        self.ref = cast("PrimitiveRef[Value] | ViewRef[View]", ref)
        self.children = (cast("PrimitiveRef[Value] | ViewRef[View]", ref),)

    def execute(self, context: Context) -> bool:
        """Execute existence check.

        Args:
            context: Execution context

        Returns:
            True if location exists, False otherwise
        """
        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            ref_path = self.ref.resolve(context)

            if isinstance(self.ref, PrimitiveRef):
                parent_view, key = path.navigate_value(root_view, ref_path)
                # Check if key exists
                if isinstance(parent_view, view_capabilities.Containable):
                    return key in parent_view
                raise TypeError(f"View {parent_view.__class__.__name__} is not containable")
            else:
                # ViewRef - just try to navigate
                if not ref_path:
                    return True
                path.navigate_view(root_view, ref_path)
                return True
        except (KeyError, IndexError):
            return False

    def __repr__(self) -> str:
        return f"ExistsOp({self.ref!r})"


class MissingOp(Operation[bool]):
    """Missing check operation (inverse of exists).

    Pure operation that checks if a location is missing from storage.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> missing_op = MissingOp(ref)
        >>> is_missing = missing_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PrimitiveRef[Value] | ViewRef[View] | UnionRefBases) -> None:
        """Initialize missing operation.

        Args:
            ref: Reference to check
        """
        self.ref = cast("PrimitiveRef[Value] | ViewRef[View]", ref)
        self.children = (cast("PrimitiveRef[Value] | ViewRef[View]", ref),)

    def execute(self, context: Context) -> bool:
        """Execute missing check.

        Args:
            context: Execution context

        Returns:
            True if location is missing, False otherwise
        """
        exists_op = ExistsOp(self.ref)
        return not exists_op.execute(context)

    def __repr__(self) -> str:
        return f"MissingOp({self.ref!r})"


class LengthOp(Operation[int | SpecialValue]):
    """Length query operation for containers.

    Pure operation that returns the length of a container.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> len_op = LengthOp(list_ref)
        >>> length = len_op.execute(ctx)  # Returns int
    """

    def __init__(self, ref: ViewRef[view_capabilities.Sizeable] | UnionRefBases) -> None:
        """Initialize length operation.

        Args:
            ref: View reference to query
        """
        self.ref = cast("ViewRef[view_capabilities.Sizeable]", ref)
        self.children = (cast("ViewRef[view_capabilities.Sizeable]", ref),)

    def execute(self, context: Context) -> int | SpecialValue:
        """Execute length query.

        Args:
            context: Execution context

        Returns:
            Length of container, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Sizeable):
                return len(view)

            raise TypeError(f"View {view.__class__.__name__} is not sizeable")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"LengthOp({self.ref!r})"


# =============================================================================
# SEQUENCE OPERATIONS
# =============================================================================


class MapOp[T, R](Operation[list[R] | SpecialValue]):
    """Map operation for sequences.

    Applies a function to each element of a sequence.

    Type Parameters:
        T: Type of input elements
        R: Type of output elements
        ContextT: Execution context type

    Example:
        >>> map_op = MapOp(list_ref, lambda x: x * 2)
        >>> result = map_op.execute(ctx)  # Returns list[R]
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        func: Callable[[T], R],
    ) -> None:
        """Initialize map operation.

        Args:
            ref: Sequence reference to map over
            func: Function to apply to each element
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.func = func
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> list[R] | SpecialValue:
        """Execute map operation.

        Args:
            context: Execution context

        Returns:
            List of transformed elements
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                return [self.func(item) for item in data]

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"MapOp({self.ref!r}, {self.func!r})"


class FilterOp[T](Operation[list[T] | SpecialValue]):
    """Filter operation for sequences.

    Filters elements based on a predicate.

    Type Parameters:
        T: Type of elements
        ContextT: Execution context type

    Example:
        >>> filter_op = FilterOp(list_ref, lambda x: x > 10)
        >>> result = filter_op.execute(ctx)  # Returns filtered list
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize filter operation.

        Args:
            ref: Sequence reference to filter
            predicate: Function that returns True for elements to keep
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> list[T] | SpecialValue:
        """Execute filter operation.

        Args:
            context: Execution context

        Returns:
            List of filtered elements
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                return [item for item in data if self.predicate(item)]

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"FilterOp({self.ref!r}, {self.predicate!r})"


class ReduceOp[T, R](Operation[R | SpecialValue]):
    """Reduce operation for sequences.

    Reduces a sequence to a single value using a reducer function.

    Type Parameters:
        T: Type of sequence elements
        R: Type of result
        ContextT: Execution context type

    Example:
        >>> reduce_op = ReduceOp(list_ref, lambda acc, x: acc + x, 0)
        >>> result = reduce_op.execute(ctx)  # Returns R
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        func: Callable[[R, T], R],
        initial: R,
    ) -> None:
        """Initialize reduce operation.

        Args:
            ref: Sequence reference to reduce
            func: Reducer function (accumulator, element) -> accumulator
            initial: Initial accumulator value
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.func = func
        self.initial = initial
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> R | SpecialValue:
        """Execute reduce operation.

        Args:
            context: Execution context

        Returns:
            Reduced value
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                return functools_reduce(self.func, data, self.initial)

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ReduceOp({self.ref!r}, {self.func!r}, {self.initial!r})"


class IndexOp[T](Operation[int]):
    """Index operation for sequences.

    Finds the index of a value in a sequence.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements
        ContextT: Execution context type

    Example:
        >>> index_op = IndexOp(list_ref, "apple")
        >>> idx = index_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        value: T,
    ) -> None:
        """Initialize index operation.

        Args:
            ref: Sequence reference to search
            value: Value to find
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.value = value
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int:
        """Execute index operation.

        Args:
            context: Execution context

        Returns:
            Index of value

        Raises:
            ValueError: If value not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            return list(data).index(self.value)

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"IndexOp({self.ref!r}, {self.value!r})"


class CountOp[T](Operation[int | SpecialValue]):
    """Count operation for sequences.

    Counts occurrences of a value in a sequence.

    Type Parameters:
        T: Type of elements
        ContextT: Execution context type

    Example:
        >>> count_op = CountOp(list_ref, "apple")
        >>> n = count_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        value: T,
    ) -> None:
        """Initialize count operation.

        Args:
            ref: Sequence reference to count in
            value: Value to count
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.value = value
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int | SpecialValue:
        """Execute count operation.

        Args:
            context: Execution context

        Returns:
            Count of occurrences
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                return list(data).count(self.value)

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"CountOp({self.ref!r}, {self.value!r})"


class FindOp[T](Operation[T]):
    """Find operation for sequences.

    Finds the first element matching a predicate.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements
        ContextT: Execution context type

    Example:
        >>> find_op = FindOp(list_ref, lambda x: x > 10)
        >>> item = find_op.execute(ctx)  # Returns T
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize find operation.

        Args:
            ref: Sequence reference to search
            predicate: Function returning True for element to find
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> T:
        """Execute find operation.

        Args:
            context: Execution context

        Returns:
            First matching element

        Raises:
            ValueError: If no element matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            for item in data:
                if self.predicate(item):
                    return item
            raise ValueError("No element matches predicate")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindOp({self.ref!r}, {self.predicate!r})"


class FindIndexOp[T](Operation[int]):
    """Find index operation for sequences.

    Finds the index of the first element matching a predicate.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements
        ContextT: Execution context type

    Example:
        >>> find_idx_op = FindIndexOp(list_ref, lambda x: x > 10)
        >>> idx = find_idx_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize find index operation.

        Args:
            ref: Sequence reference to search
            predicate: Function returning True for element to find
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int:
        """Execute find index operation.

        Args:
            context: Execution context

        Returns:
            Index of first matching element

        Raises:
            ValueError: If no element matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            for i, item in enumerate(data):
                if self.predicate(item):
                    return i
            raise ValueError("No element matches predicate")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindIndexOp({self.ref!r}, {self.predicate!r})"


# =============================================================================
# MAPPING OPERATIONS
# =============================================================================


class KeysOp[K](Operation[list[K] | SpecialValue]):
    """Keys operation for mappings.

    Returns all keys of a mapping.

    Type Parameters:
        K: Type of keys
        ContextT: Execution context type

    Example:
        >>> keys_op = KeysOp(dict_ref)
        >>> keys = keys_op.execute(ctx)  # Returns list[K]
    """

    def __init__(
        self, ref: ViewRef[view_capabilities.Convertible[dict[K, object]]] | UnionRefBases
    ) -> None:
        """Initialize keys operation.

        Args:
            ref: Mapping reference to query
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, object]]]", ref)
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, object]]]", ref),)

    def execute(self, context: Context) -> list[K] | SpecialValue:
        """Execute keys operation.

        Args:
            context: Execution context

        Returns:
            List of keys
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return list(data.keys())
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"KeysOp({self.ref!r})"


class ValuesOp[V](Operation[list[V] | SpecialValue]):
    """Values operation for mappings.

    Returns all values of a mapping.

    Type Parameters:
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> values_op = ValuesOp(dict_ref)
        >>> values = values_op.execute(ctx)  # Returns list[V]
    """

    def __init__(
        self, ref: ViewRef[view_capabilities.Convertible[dict[object, V]]] | UnionRefBases
    ) -> None:
        """Initialize values operation.

        Args:
            ref: Mapping reference to query
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref)
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref),)

    def execute(self, context: Context) -> list[V] | SpecialValue:
        """Execute values operation.

        Args:
            context: Execution context

        Returns:
            List of values
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return list(data.values())
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ValuesOp({self.ref!r})"


class ItemsOp[K, V](Operation[list[tuple[K, V]] | SpecialValue]):
    """Items operation for mappings.

    Returns all key-value pairs of a mapping.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> items_op = ItemsOp(dict_ref)
        >>> items = items_op.execute(ctx)  # Returns list[tuple[K, V]]
    """

    def __init__(
        self, ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases
    ) -> None:
        """Initialize items operation.

        Args:
            ref: Mapping reference to query
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> list[tuple[K, V]] | SpecialValue:
        """Execute items operation.

        Args:
            context: Execution context

        Returns:
            List of (key, value) pairs
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return list(data.items())
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ItemsOp({self.ref!r})"


class MapValuesOp[K, V, R](Operation[dict[K, R] | SpecialValue]):
    """Map values operation for mappings.

    Applies a function to each value in a mapping.

    Type Parameters:
        K: Type of keys
        V: Type of input values
        R: Type of output values
        ContextT: Execution context type

    Example:
        >>> map_op = MapValuesOp(dict_ref, lambda x: x * 2)
        >>> result = map_op.execute(ctx)  # Returns dict[K, R]
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        func: Callable[[V], R],
    ) -> None:
        """Initialize map values operation.

        Args:
            ref: Mapping reference to map over
            func: Function to apply to each value
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.func = func
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> dict[K, R] | SpecialValue:
        """Execute map values operation.

        Args:
            context: Execution context

        Returns:
            Dict with transformed values
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return {k: self.func(v) for k, v in data.items()}
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"MapValuesOp({self.ref!r}, {self.func!r})"


class MapItemsOp[K, V, K2, V2](Operation[dict[K2, V2] | SpecialValue]):
    """Map items operation for mappings.

    Applies a function to each (key, value) pair.

    Type Parameters:
        K: Type of input keys
        V: Type of input values
        K2: Type of output keys
        V2: Type of output values
        ContextT: Execution context type

    Example:
        >>> map_op = MapItemsOp(dict_ref, lambda k, v: (k.upper(), v * 2))
        >>> result = map_op.execute(ctx)  # Returns dict[K2, V2]
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        func: Callable[[K, V], tuple[K2, V2]],
    ) -> None:
        """Initialize map items operation.

        Args:
            ref: Mapping reference to map over
            func: Function taking (key, value) returning (new_key, new_value)
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.func = func
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> dict[K2, V2] | SpecialValue:
        """Execute map items operation.

        Args:
            context: Execution context

        Returns:
            Transformed dict
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return dict(self.func(k, v) for k, v in data.items())
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"MapItemsOp({self.ref!r}, {self.func!r})"


class FilterItemsOp[K, V](Operation[dict[K, V] | SpecialValue]):
    """Filter items operation for mappings.

    Filters items based on a predicate.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> filter_op = FilterItemsOp(dict_ref, lambda k, v: v > 10)
        >>> result = filter_op.execute(ctx)  # Returns filtered dict
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        predicate: Callable[[K, V], bool],
    ) -> None:
        """Initialize filter items operation.

        Args:
            ref: Mapping reference to filter
            predicate: Function (key, value) -> bool, keep if True
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> dict[K, V] | SpecialValue:
        """Execute filter items operation.

        Args:
            context: Execution context

        Returns:
            Filtered dict
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    return {k: v for k, v in data.items() if self.predicate(k, v)}
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"FilterItemsOp({self.ref!r}, {self.predicate!r})"


class ReduceItemsOp[K, V, R](Operation[R | SpecialValue]):
    """Reduce items operation for mappings.

    Reduces a mapping to a single value.

    Type Parameters:
        K: Type of keys
        V: Type of values
        R: Type of result
        ContextT: Execution context type

    Example:
        >>> reduce_op = ReduceItemsOp(dict_ref, lambda acc, k, v: acc + v, 0)
        >>> result = reduce_op.execute(ctx)  # Returns R
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        func: Callable[[R, K, V], R],
        initial: R,
    ) -> None:
        """Initialize reduce items operation.

        Args:
            ref: Mapping reference to reduce
            func: Reducer function (accumulator, key, value) -> accumulator
            initial: Initial accumulator value
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.func = func
        self.initial = initial
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> R | SpecialValue:
        """Execute reduce items operation.

        Args:
            context: Execution context

        Returns:
            Reduced value
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                data = view.extract()
                if isinstance(data, dict):
                    result = self.initial
                    for k, v in data.items():
                        result = self.func(result, k, v)
                    return result
                raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ReduceItemsOp({self.ref!r}, {self.func!r}, {self.initial!r})"


class FindKeyOp[K, V](Operation[K]):
    """Find key operation for mappings.

    Finds the first key whose value matches a predicate.
    Raises ValueError if not found.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> find_op = FindKeyOp(dict_ref, lambda v: v > 100)
        >>> key = find_op.execute(ctx)  # Returns K
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        predicate: Callable[[V], bool],
    ) -> None:
        """Initialize find key operation.

        Args:
            ref: Mapping reference to search
            predicate: Function applied to values, return True to match
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> K:
        """Execute find key operation.

        Args:
            context: Execution context

        Returns:
            First key whose value matches

        Raises:
            ValueError: If no value matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            if isinstance(data, dict):
                for k, v in data.items():
                    if self.predicate(v):
                        return k
                raise ValueError("No value matches predicate")
            raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindKeyOp({self.ref!r}, {self.predicate!r})"


class FindValueOp[V](Operation[V]):
    """Find value operation for mappings.

    Finds the first value matching a predicate.
    Raises ValueError if not found.

    Type Parameters:
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> find_op = FindValueOp(dict_ref, lambda v: v > 100)
        >>> value = find_op.execute(ctx)  # Returns V
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[object, V]]] | UnionRefBases,
        predicate: Callable[[V], bool],
    ) -> None:
        """Initialize find value operation.

        Args:
            ref: Mapping reference to search
            predicate: Function applied to values, return True to match
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref),)

    def execute(self, context: Context) -> V:
        """Execute find value operation.

        Args:
            context: Execution context

        Returns:
            First matching value

        Raises:
            ValueError: If no value matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            if isinstance(data, dict):
                for v in data.values():
                    if self.predicate(v):
                        return v
                raise ValueError("No value matches predicate")
            raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindValueOp({self.ref!r}, {self.predicate!r})"


class FindItemOp[K, V](Operation[tuple[K, V]]):
    """Find item operation for mappings.

    Finds the first (key, value) pair matching a predicate.
    Raises ValueError if not found.

    Type Parameters:
        K: Type of keys
        V: Type of values
        ContextT: Execution context type

    Example:
        >>> find_op = FindItemOp(dict_ref, lambda k, v: k.startswith("user") and v > 0)
        >>> item = find_op.execute(ctx)  # Returns tuple[K, V]
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        predicate: Callable[[K, V], bool],
    ) -> None:
        """Initialize find item operation.

        Args:
            ref: Mapping reference to search
            predicate: Function (key, value) -> bool
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> tuple[K, V]:
        """Execute find item operation.

        Args:
            context: Execution context

        Returns:
            First matching (key, value) pair

        Raises:
            ValueError: If no item matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Convertible):
            data = view.extract()
            if isinstance(data, dict):
                for k, v in data.items():
                    if self.predicate(k, v):
                        return (k, v)
                raise ValueError("No item matches predicate")
            raise TypeError(f"Extracted data is not a dict: {type(data).__name__}")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindItemOp({self.ref!r}, {self.predicate!r})"
