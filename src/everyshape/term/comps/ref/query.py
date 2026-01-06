"""Mapping query operations for LValue references.

This module provides mapping query operations:

Operations:
    - KeysOp: Get all keys
    - ValuesOp: Get all values
    - ItemsOp: Get all key-value pairs
    - MappingGetOp: Get value by key with default
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape import NOT_SET, NotSet
from everyshape.loc import path
from everyshape.storage import StorageKeyError
from everyshape.term import Operation, RValue, ViewRef
from everyshape.types import Empty, SpecialValue
from everyshape.view import capabilities as view_capabilities


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "ItemsOp",
    "KeysOp",
    "MappingGetOp",
    "ValuesOp",
]


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


class MappingGetOp[K, V](Operation[V | SpecialValue]):
    """Get operation for mapping containers.

    Gets a value by key from a mapping, returning a default if not found.
    This operates on the container level (ViewRef) rather than individual items.

    Type Parameters:
        K: Type of keys
        V: Type of values

    Example:
        >>> get_op = MappingGetOp(dict_ref, "key", "default")
        >>> value = get_op.execute(ctx)  # Returns V or default
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Subscriptable[K, V]] | UnionRefBases,
        key: RValue[K | SpecialValue],
        default: RValue[V | SpecialValue] | NotSet = NOT_SET,
    ) -> None:
        """Initialize mapping get operation.

        Args:
            ref: Mapping reference to get from
            key: Key to look up
            default: Value to return if key not found (default: Empty)
        """
        self.ref = cast("ViewRef[view_capabilities.Subscriptable[K, V]]", ref)
        self.key = key
        self.default = default
        self.children = (cast("ViewRef[view_capabilities.Subscriptable[K, V]]", ref),)

    def execute(self, context: Context) -> V | SpecialValue:
        """Execute get operation.

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
        return f"MappingGetOp({self.ref!r}, {self.key!r}, {self.default!r})"
