"""Higher-order/functional operations for LValue references.

This module provides functional operations for refs:

Sequence Operations:
    - MapOp: Map function over sequence
    - FilterOp: Filter sequence by predicate
    - ReduceOp: Reduce sequence to single value

Mapping Operations:
    - MapValuesOp: Map function over values
    - MapItemsOp: Map function over items
    - FilterItemsOp: Filter items by predicate
    - ReduceItemsOp: Reduce items to single value
"""

from __future__ import annotations

from functools import reduce as functools_reduce
from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.term.term import Operation, ViewRef
from everyshape.types import Empty, SpecialValue
from everyshape.view import capabilities as view_capabilities


if TYPE_CHECKING:
    from collections.abc import Callable

    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "FilterItemsOp",
    "FilterOp",
    "MapItemsOp",
    "MapOp",
    "MapValuesOp",
    "ReduceItemsOp",
    "ReduceOp",
]


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


# =============================================================================
# MAPPING OPERATIONS
# =============================================================================


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
