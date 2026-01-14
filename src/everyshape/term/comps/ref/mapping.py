"""Mapping operations for LValue references.

This module provides operations for mapping containers (dicts, etc.).

Commands (mutations):
    - SetByKeyCmd: Set value at key
    - RemoveByKeyCmd: Remove entry by key

Operations (queries):
    - GetByKeyOp: Get value by key with optional default
    - KeysOp: Get all keys
    - ValuesOp: Get all values
    - ItemsOp: Get all key-value pairs

Search Operations:
    - FindKeyByPredicateOp: Find key whose value matches predicate
    - FindValueByPredicateOp: Find value matching predicate
    - FindItemByPredicateOp: Find (key, value) pair matching predicate

Functional Operations:
    - MapValuesOp: Transform values
    - MapItemsOp: Transform key-value pairs
    - FilterItemsOp: Keep items matching predicate
    - ReduceItemsOp: Reduce to single value
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape import NOT_SET, NotSet
from everyshape.loc import path
from everyshape.storage import StorageKeyError
from everyshape.term import Command, Operation, RValue, ViewRef
from everyshape.typing import Empty, Sentinel, Value
from everyshape.view import capabilities as view_capabilities


if TYPE_CHECKING:
    from collections.abc import Callable

    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "FilterItemsOp",
    "FindItemByPredicateOp",
    "FindKeyByPredicateOp",
    "FindValueByPredicateOp",
    "GetByKeyOp",
    "ItemsOp",
    "KeysOp",
    "MapItemsOp",
    "MapValuesOp",
    "ReduceItemsOp",
    "RemoveByKeyCmd",
    "SetByKeyCmd",
    "ValuesOp",
]


# =============================================================================
# MUTATION COMMANDS
# =============================================================================


class SetByKeyCmd[K, V: Value](Command[V]):
    """Set a value at a key in a mapping.

    Impure command that sets a value at a key in a mapping container.
    Returns the set value.

    Type Parameters:
        K: Type of key
        V: Type of value

    Example:
        >>> set_cmd = SetByKeyCmd(dict_ref, literal("key"), literal("value"))
        >>> set_value = set_cmd.execute(ctx)  # Returns "value"
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Assignable[K, V]] | UnionRefBases,
        key: RValue[K | Sentinel],
        value: RValue[V | Sentinel],
    ) -> None:
        """Initialize set by key command.

        Args:
            ref: Mapping reference to set value in
            key: Key to set (wrapped in RValue)
            value: Value to set (wrapped in RValue)
        """
        self.ref = cast("ViewRef[view_capabilities.Assignable[K, V]]", ref)
        self.key = key
        self.value_expr = value
        self.children = (cast("ViewRef[view_capabilities.Assignable[K, V]]", ref), value)

    def execute(self, context: Context) -> V:
        """Execute set by key command.

        Args:
            context: Execution context with transaction

        Returns:
            The set value
        """
        view_path = self.ref.resolve(context)

        key = self.key.execute(context)
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, NaN, etc): {value}")

        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, view_capabilities.Assignable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Assignable protocol."
            )

        view[key] = value
        return value

    def __repr__(self) -> str:
        return f"SetByKeyCmd({self.ref!r}, {self.key!r}, {self.value_expr!r})"


class RemoveByKeyCmd[K](Command[None]):
    """Remove an entry by key from a mapping.

    Impure command that removes a key from a mapping container.
    Raises KeyError if key not found.
    Returns None.

    Type Parameters:
        K: Type of key

    Example:
        >>> remove_cmd = RemoveByKeyCmd(dict_ref, literal("key"))
        >>> remove_cmd.execute(ctx)  # Returns None
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Deletable[K]] | UnionRefBases,
        key: RValue[K | Sentinel],
    ) -> None:
        """Initialize remove by key command.

        Args:
            ref: Mapping reference to remove key from
            key: Key to remove (wrapped in RValue)
        """
        self.ref = cast("ViewRef[view_capabilities.Deletable[K]]", ref)
        self.key = key
        self.children = (cast("ViewRef[view_capabilities.Deletable[K]]", ref),)

    def execute(self, context: Context) -> None:
        """Execute remove by key command.

        Args:
            context: Execution context with transaction

        Returns:
            None

        Raises:
            KeyError: If key not in mapping
        """
        view_path = self.ref.resolve(context)
        key = self.key.execute(context)

        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, view_capabilities.Deletable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Deletable protocol."
            )

        del view[key]
        return None

    def __repr__(self) -> str:
        return f"RemoveByKeyCmd({self.ref!r}, {self.key!r})"


# =============================================================================
# QUERY OPERATIONS
# =============================================================================


class GetByKeyOp[K, V](Operation[V | Sentinel]):
    """Get a value by key from a mapping.

    Pure operation that gets a value by key, returning a default if not found.
    This operates on the container level (ViewRef) rather than individual items.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> get_op = GetByKeyOp(dict_ref, literal("key"), literal("default"))
        >>> value = get_op.execute(ctx)  # Returns V or default
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Subscriptable[K, V]] | UnionRefBases,
        key: RValue[K | Sentinel],
        default: RValue[V | Sentinel] | NotSet = NOT_SET,
    ) -> None:
        """Initialize get by key operation.

        Args:
            ref: Mapping reference to get from
            key: Key to look up
            default: Value to return if key not found (default: Empty)
        """
        self.ref = cast("ViewRef[view_capabilities.Subscriptable[K, V]]", ref)
        self.key = key
        self.default = default
        self.children = (cast("ViewRef[view_capabilities.Subscriptable[K, V]]", ref),)

    def execute(self, context: Context) -> V | Sentinel:
        """Execute get by key operation.

        Args:
            context: Execution context

        Returns:
            Value at key, or default if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        key = self.key.execute(context)

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if isinstance(view, view_capabilities.Subscriptable):
            try:
                return view[key]
            except (KeyError, IndexError, StorageKeyError) as e:
                if not isinstance(self.default, NotSet):
                    return self.default.execute(context)
                raise e

        raise TypeError(f"View {view.__class__.__name__} is not subscriptable")

    def __repr__(self) -> str:
        return f"GetByKeyOp({self.ref!r}, {self.key!r}, {self.default!r})"


class KeysOp[K](Operation[list[K] | Sentinel]):
    """Get all keys from a mapping.

    Pure operation that returns all keys of a mapping as a list.

    Type Parameters:
        K: Type of keys

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

    def execute(self, context: Context) -> list[K] | Sentinel:
        """Execute keys operation.

        Args:
            context: Execution context

        Returns:
            List of keys, or Empty if not found
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


class ValuesOp[V](Operation[list[V] | Sentinel]):
    """Get all values from a mapping.

    Pure operation that returns all values of a mapping as a list.

    Type Parameters:
        V: Type of values

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

    def execute(self, context: Context) -> list[V] | Sentinel:
        """Execute values operation.

        Args:
            context: Execution context

        Returns:
            List of values, or Empty if not found
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


class ItemsOp[K, V](Operation[list[tuple[K, V]] | Sentinel]):
    """Get all key-value pairs from a mapping.

    Pure operation that returns all key-value pairs as a list of tuples.

    Type Parameters:
        K: Type of keys
        V: Type of values

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

    def execute(self, context: Context) -> list[tuple[K, V]] | Sentinel:
        """Execute items operation.

        Args:
            context: Execution context

        Returns:
            List of (key, value) pairs, or Empty if not found
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


# =============================================================================
# SEARCH OPERATIONS
# =============================================================================


class FindKeyByPredicateOp[K, V](Operation[K]):
    """Find a key whose value matches a predicate.

    Pure operation that searches a mapping and returns the first key
    for which the value satisfies the predicate.
    Raises ValueError if not found.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> find_op = FindKeyByPredicateOp(dict_ref, lambda v: v > 100)
        >>> key = find_op.execute(ctx)  # Returns K
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        predicate: Callable[[V], bool],
    ) -> None:
        """Initialize find key by predicate operation.

        Args:
            ref: Mapping reference to search
            predicate: Function applied to values, return True to match
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> K:
        """Execute find key by predicate operation.

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
        return f"FindKeyByPredicateOp({self.ref!r}, {self.predicate!r})"


class FindValueByPredicateOp[V](Operation[V]):
    """Find the first value in a mapping matching a predicate.

    Pure operation that searches a mapping's values and returns the first
    one for which the predicate returns True.
    Raises ValueError if not found.

    Type Parameters:
        V: Type of values

    Example:
        >>> find_op = FindValueByPredicateOp(dict_ref, lambda v: v > 100)
        >>> value = find_op.execute(ctx)  # Returns V
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[object, V]]] | UnionRefBases,
        predicate: Callable[[V], bool],
    ) -> None:
        """Initialize find value by predicate operation.

        Args:
            ref: Mapping reference to search
            predicate: Function applied to values, return True to match
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[object, V]]]", ref),)

    def execute(self, context: Context) -> V:
        """Execute find value by predicate operation.

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
        return f"FindValueByPredicateOp({self.ref!r}, {self.predicate!r})"


class FindItemByPredicateOp[K, V](Operation[tuple[K, V]]):
    """Find the first (key, value) pair in a mapping matching a predicate.

    Pure operation that searches a mapping and returns the first (key, value)
    pair for which the predicate returns True.
    Raises ValueError if not found.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> find_op = FindItemByPredicateOp(
        ...     dict_ref, lambda k, v: k.startswith("user") and v > 0
        ... )
        >>> item = find_op.execute(ctx)  # Returns tuple[K, V]
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Convertible[dict[K, V]]] | UnionRefBases,
        predicate: Callable[[K, V], bool],
    ) -> None:
        """Initialize find item by predicate operation.

        Args:
            ref: Mapping reference to search
            predicate: Function (key, value) -> bool
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref)
        self.predicate = predicate
        self.children = (cast("ViewRef[view_capabilities.Convertible[dict[K, V]]]", ref),)

    def execute(self, context: Context) -> tuple[K, V]:
        """Execute find item by predicate operation.

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
        return f"FindItemByPredicateOp({self.ref!r}, {self.predicate!r})"


# =============================================================================
# FUNCTIONAL OPERATIONS
# =============================================================================


class MapValuesOp[K, V, R](Operation[dict[K, R] | Sentinel]):
    """Map a function over mapping values.

    Pure operation that applies a function to each value in a mapping.

    Type Parameters:
        K: Type of keys
        V: Type of input values
        R: Type of output values

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

    def execute(self, context: Context) -> dict[K, R] | Sentinel:
        """Execute map values operation.

        Args:
            context: Execution context

        Returns:
            Dict with transformed values, or Empty if not found
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


class MapItemsOp[K, V, K2, V2](Operation[dict[K2, V2] | Sentinel]):
    """Map a function over mapping items.

    Pure operation that applies a function to each (key, value) pair.

    Type Parameters:
        K: Type of input keys
        V: Type of input values
        K2: Type of output keys
        V2: Type of output values

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

    def execute(self, context: Context) -> dict[K2, V2] | Sentinel:
        """Execute map items operation.

        Args:
            context: Execution context

        Returns:
            Transformed dict, or Empty if not found
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


class FilterItemsOp[K, V](Operation[dict[K, V] | Sentinel]):
    """Filter mapping items by predicate.

    Pure operation that keeps items matching a predicate.

    Type Parameters:
        K: Type of keys
        V: Type of values

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

    def execute(self, context: Context) -> dict[K, V] | Sentinel:
        """Execute filter items operation.

        Args:
            context: Execution context

        Returns:
            Filtered dict, or Empty if not found
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


class ReduceItemsOp[K, V, R](Operation[R | Sentinel]):
    """Reduce mapping items to single value.

    Pure operation that reduces a mapping to a single value.

    Type Parameters:
        K: Type of keys
        V: Type of values
        R: Type of result

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

    def execute(self, context: Context) -> R | Sentinel:
        """Execute reduce items operation.

        Args:
            context: Execution context

        Returns:
            Reduced value, or Empty if not found
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
