"""Sequence operations for LValue references.

This module provides operations for sequence containers (lists, tuples, etc.).

Commands (mutations):
    - AppendValueCmd: Append value to end of sequence
    - InsertAtIndexCmd: Insert value at specific index
    - PopByIndexCmd: Remove and return value at index

Operations (queries):
    - IndexOfValueOp: Find index of a specific value
    - CountOfValueOp: Count occurrences of a value

Search Operations:
    - FindByPredicateOp: Find first element matching predicate
    - FindIndexByPredicateOp: Find index of first match

Functional Operations:
    - MapOp: Transform each element
    - FilterOp: Keep elements matching predicate
    - ReduceOp: Reduce to single value
"""

from __future__ import annotations

from functools import reduce as functools_reduce
from typing import TYPE_CHECKING, cast

import pv.traits as view_traits
from pv.loc import path
from pv.traits import Appendable, Poppable
from pv.view import View

from everyabc import EMPTY, Command, Morphism, Operation, Sentinel, Term


if TYPE_CHECKING:
    from collections.abc import Callable

    from every_pv.ref import PVViewRef
    from everyabc import Context

type UnionRefBases = None


__all__ = [
    "AppendValueCmd",
    "CountOfValueOp",
    "FilterOp",
    "FindByPredicateOp",
    "FindIndexByPredicateOp",
    "IndexOfValueOp",
    "InsertAtIndexCmd",
    "MapOp",
    "PopByIndexCmd",
    "ReduceOp",
]


# =============================================================================
# MUTATION COMMANDS
# =============================================================================


class AppendValueCmd[T](Command, Morphism[T]):
    """Append a value to the end of a sequence.

    Impure command that appends an item to a list or similar sequence.
    Returns the appended value.

    Type Parameters:
        T: Type of item to append

    Example:
        >>> append_cmd = AppendValueCmd(list_ref, literal(42))
        >>> appended = append_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: PVViewRef[Appendable] | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize append value command.

        Args:
            ref: Sequence reference to append to
            value: Value to append (wrapped in Term)
        """
        self.ref = cast("PVViewRef[Appendable]", ref)
        self.value_expr = value
        self.children = (cast("PVViewRef[Appendable]", ref), value)

    def execute(self, context: Context) -> T:
        """Execute append value command.

        Args:
            context: Execution context with transaction

        Returns:
            The appended value
        """
        view_path = self.ref.resolve(context)
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot append special values (Empty, Invalid, etc): {value}")

        root_view = context.get(View, shape=self.ref.get_root_shape())

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, Appendable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Appendable protocol."
            )

        view.append(value)
        return value

    def __repr__(self) -> str:
        return f"AppendValueCmd({self.ref!r}, {self.value_expr!r})"


class InsertAtIndexCmd[T](Command, Morphism[T]):
    """Insert a value at a specific index in a sequence.

    Impure command that inserts an item at a specific index.
    Returns the inserted value.

    Type Parameters:
        T: Type of item to insert

    Example:
        >>> insert_cmd = InsertAtIndexCmd(list_ref, literal(0), literal(42))
        >>> inserted = insert_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: PVViewRef | UnionRefBases,
        index: Term[int | Sentinel],
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize insert at index command.

        Args:
            ref: Sequence reference to insert into
            index: Index to insert at (wrapped in Term)
            value: Value to insert (wrapped in Term)
        """
        self.ref = cast("PVViewRef", ref)
        self.index_expr = index
        self.value_expr = value
        self.children = (cast("PVViewRef", ref), index, value)

    def execute(self, context: Context) -> T:
        """Execute insert at index command.

        Args:
            context: Execution context with transaction

        Returns:
            The inserted value
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"InsertAtIndexCmd({self.ref!r}, {self.index_expr!r}, {self.value_expr!r})"


class PopByIndexCmd[T](Command, Morphism[T]):
    """Pop a value from a sequence by index.

    Impure command that removes and returns an item by index.
    Default index is -1 (last item).
    Returns the popped value.

    Type Parameters:
        T: Type of item to pop

    Example:
        >>> pop_cmd = PopByIndexCmd(list_ref)
        >>> popped = pop_cmd.execute(ctx)  # Returns last item
        >>> pop_cmd = PopByIndexCmd(list_ref, literal(0))
        >>> first = pop_cmd.execute(ctx)  # Returns first item
    """

    def __init__(
        self,
        ref: PVViewRef | UnionRefBases,
        index: Term[int | Sentinel] | None = None,
    ) -> None:
        """Initialize pop by index command.

        Args:
            ref: Sequence reference to pop from
            index: Index to pop from (default: -1, last item)
        """
        self.ref = cast("PVViewRef", ref)
        self.index_expr = index
        self.children = (
            (cast("PVViewRef", ref), index) if index is not None else (cast("PVViewRef", ref),)
        )

    def execute(self, context: Context) -> T:
        """Execute pop by index command.

        Args:
            context: Execution context with transaction

        Returns:
            The popped value
        """
        view_path = self.ref.resolve(context)

        if self.index_expr is not None:
            index = self.index_expr.execute(context)
            if isinstance(index, Sentinel):
                raise ValueError(f"Cannot use special value as index: {index}")
        else:
            index = -1

        root_view = context.get(View, shape=self.ref.get_root_shape())

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, Poppable):
            raise TypeError(f"View {view.__class__.__name__} does not implement Poppable protocol.")

        return view.pop(index)

    def __repr__(self) -> str:
        return f"PopByIndexCmd({self.ref!r}, {self.index_expr!r})"


# =============================================================================
# QUERY OPERATIONS
# =============================================================================


class IndexOfValueOp[T](Operation, Morphism[int]):
    """Find the index of a specific value in a sequence.

    Pure operation that finds the index of a value.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements

    Example:
        >>> index_op = IndexOfValueOp(list_ref, "apple")
        >>> idx = index_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        value: T,
    ) -> None:
        """Initialize index of value operation.

        Args:
            ref: Sequence reference to search
            value: Value to find
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.value = value
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int:
        """Execute index of value operation.

        Args:
            context: Execution context

        Returns:
            Index of value

        Raises:
            ValueError: If value not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_traits.Convertible):
            data = view.extract()
            return list(data).index(self.value)

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"IndexOfValueOp({self.ref!r}, {self.value!r})"


class CountOfValueOp[T](Operation, Morphism[int | Sentinel]):
    """Count occurrences of a specific value in a sequence.

    Pure operation that counts how many times a value appears.

    Type Parameters:
        T: Type of elements

    Example:
        >>> count_op = CountOfValueOp(list_ref, "apple")
        >>> n = count_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        value: T,
    ) -> None:
        """Initialize count of value operation.

        Args:
            ref: Sequence reference to count in
            value: Value to count
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.value = value
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int | Sentinel:
        """Execute count of value operation.

        Args:
            context: Execution context

        Returns:
            Count of occurrences, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Convertible):
                data = view.extract()
                return list(data).count(self.value)

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"CountOfValueOp({self.ref!r}, {self.value!r})"


# =============================================================================
# SEARCH OPERATIONS
# =============================================================================


class FindByPredicateOp[T](Operation, Morphism[T]):
    """Find the first element matching a predicate.

    Pure operation that searches a sequence and returns the first element
    for which the predicate returns True.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements

    Example:
        >>> find_op = FindByPredicateOp(list_ref, lambda x: x > 10)
        >>> item = find_op.execute(ctx)  # Returns T
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize find by predicate operation.

        Args:
            ref: Sequence reference to search
            predicate: Function returning True for element to find
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> T:
        """Execute find by predicate operation.

        Args:
            context: Execution context

        Returns:
            First matching element

        Raises:
            ValueError: If no element matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_traits.Convertible):
            data = view.extract()
            for item in data:
                if self.predicate(item):
                    return item
            raise ValueError("No element matches predicate")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindByPredicateOp({self.ref!r}, {self.predicate!r})"


class FindIndexByPredicateOp[T](Operation, Morphism[int]):
    """Find the index of the first element matching a predicate.

    Pure operation that searches a sequence and returns the index of the
    first element for which the predicate returns True.
    Raises ValueError if not found.

    Type Parameters:
        T: Type of elements

    Example:
        >>> find_idx_op = FindIndexByPredicateOp(list_ref, lambda x: x > 10)
        >>> idx = find_idx_op.execute(ctx)  # Returns int
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize find index by predicate operation.

        Args:
            ref: Sequence reference to search
            predicate: Function returning True for element to find
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> int:
        """Execute find index by predicate operation.

        Args:
            context: Execution context

        Returns:
            Index of first matching element

        Raises:
            ValueError: If no element matches
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_traits.Convertible):
            data = view.extract()
            for i, item in enumerate(data):
                if self.predicate(item):
                    return i
            raise ValueError("No element matches predicate")

        raise TypeError(f"View {view.__class__.__name__} is not convertible")

    def __repr__(self) -> str:
        return f"FindIndexByPredicateOp({self.ref!r}, {self.predicate!r})"


# =============================================================================
# FUNCTIONAL OPERATIONS
# =============================================================================


class MapOp[T, R](Operation, Morphism[list[R] | Sentinel]):
    """Map a function over sequence elements.

    Pure operation that applies a function to each element.

    Type Parameters:
        T: Type of input elements
        R: Type of output elements

    Example:
        >>> map_op = MapOp(list_ref, lambda x: x * 2)
        >>> result = map_op.execute(ctx)  # Returns list[R]
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        func: Callable[[T], R],
    ) -> None:
        """Initialize map operation.

        Args:
            ref: Sequence reference to map over
            func: Function to apply to each element
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.func = func
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> list[R] | Sentinel:
        """Execute map operation.

        Args:
            context: Execution context

        Returns:
            List of transformed elements, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Convertible):
                data = view.extract()
                return [self.func(item) for item in data]

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"MapOp({self.ref!r}, {self.func!r})"


class FilterOp[T](Operation, Morphism[list[T] | Sentinel]):
    """Filter sequence elements by predicate.

    Pure operation that keeps elements matching a predicate.

    Type Parameters:
        T: Type of elements

    Example:
        >>> filter_op = FilterOp(list_ref, lambda x: x > 10)
        >>> result = filter_op.execute(ctx)  # Returns filtered list
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        predicate: Callable[[T], bool],
    ) -> None:
        """Initialize filter operation.

        Args:
            ref: Sequence reference to filter
            predicate: Function that returns True for elements to keep
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.predicate = predicate
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> list[T] | Sentinel:
        """Execute filter operation.

        Args:
            context: Execution context

        Returns:
            List of filtered elements, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Convertible):
                data = view.extract()
                return [item for item in data if self.predicate(item)]

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"FilterOp({self.ref!r}, {self.predicate!r})"


class ReduceOp[T, R](Operation, Morphism[R | Sentinel]):
    """Reduce sequence to single value.

    Pure operation that reduces a sequence using a reducer function.

    Type Parameters:
        T: Type of sequence elements
        R: Type of result

    Example:
        >>> reduce_op = ReduceOp(list_ref, lambda acc, x: acc + x, 0)
        >>> result = reduce_op.execute(ctx)  # Returns R
    """

    def __init__(
        self,
        ref: PVViewRef[view_traits.Convertible[list[T]]] | UnionRefBases,
        func: Callable[[R, T], R],
        initial: R,
    ) -> None:
        """Initialize reduce operation.

        Args:
            ref: Sequence reference to reduce
            func: Reducer function (accumulator, element) -> accumulator
            initial: Initial accumulator value
        """
        self.ref = cast("PVViewRef[view_traits.Convertible[list[T]]]", ref)
        self.func = func
        self.initial = initial
        self.children = (cast("PVViewRef[view_traits.Convertible[list[T]]]", ref),)

    def execute(self, context: Context) -> R | Sentinel:
        """Execute reduce operation.

        Args:
            context: Execution context

        Returns:
            Reduced value, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get(View, shape=self.ref.get_root_shape())

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Convertible):
                data = view.extract()
                return functools_reduce(self.func, data, self.initial)

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"ReduceOp({self.ref!r}, {self.func!r}, {self.initial!r})"
