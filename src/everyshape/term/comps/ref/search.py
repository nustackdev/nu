"""Search operations for LValue references.

This module provides search operations for refs:

Sequence Search Operations:
    - IndexOp: Find index of value
    - CountOp: Count occurrences
    - FindOp: Find first matching element
    - FindIndexOp: Find index of first match

Mapping Search Operations:
    - FindKeyOp: Find key by value predicate
    - FindValueOp: Find value by predicate
    - FindItemOp: Find item by predicate
"""

from __future__ import annotations

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
    "CountOp",
    "FindIndexOp",
    "FindItemOp",
    "FindKeyOp",
    "FindOp",
    "FindValueOp",
    "IndexOp",
]


# =============================================================================
# SEQUENCE SEARCH OPERATIONS
# =============================================================================


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
# MAPPING SEARCH OPERATIONS
# =============================================================================


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
