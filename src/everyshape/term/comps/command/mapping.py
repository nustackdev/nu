"""Mapping mutation command classes for LValue references.

This module provides mapping mutation commands:

Commands (impure mutations):
    - MappingSetCmd: Set value at key in mapping container
    - MappingRemoveCmd: Remove key from mapping container
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.types import SpecialValue, Value
from everyshape.view import capabilities as view_capabilities

from ...term import Command, RValue, ViewRef


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "MappingRemoveCmd",
    "MappingSetCmd",
]


class MappingSetCmd[K, V: Value](Command[V]):
    """Set command for mapping containers.

    Impure command that sets a value at a key in a mapping container.
    Returns the set value.

    Type Parameters:
        K: Type of key
        V: Type of value

    Example:
        >>> set_cmd = MappingSetCmd(dict_ref, "key", literal("value"))
        >>> set_value = set_cmd.execute(ctx)  # Returns "value"
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Assignable[K, V]] | UnionRefBases,
        key: K,
        value: RValue[V | SpecialValue],
    ) -> None:
        """Initialize mapping set command.

        Args:
            ref: Mapping reference to set value in
            key: Key to set
            value: Value to set (wrapped in RValue)
        """
        self.ref = cast("ViewRef[view_capabilities.Assignable[K, V]]", ref)
        self.key = key
        self.value_expr = value
        self.children = (cast("ViewRef[view_capabilities.Assignable[K, V]]", ref), value)

    def execute(self, context: Context) -> V:
        """Execute set command.

        Args:
            context: Execution context with transaction

        Returns:
            The set value
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, SpecialValue):
            raise ValueError(f"Cannot store special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Set through view
        if not isinstance(view, view_capabilities.Assignable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Assignable protocol."
            )

        view[self.key] = value
        return value

    def __repr__(self) -> str:
        return f"MappingSetCmd({self.ref!r}, {self.key!r}, {self.value_expr!r})"


class MappingRemoveCmd[K](Command[None]):
    """Remove command for mapping containers.

    Impure command that removes a key from a mapping container.
    Raises KeyError if key not found.
    Returns None.

    Type Parameters:
        K: Type of key

    Example:
        >>> remove_cmd = MappingRemoveCmd(dict_ref, "key")
        >>> remove_cmd.execute(ctx)  # Returns None
    """

    def __init__(
        self,
        ref: ViewRef[view_capabilities.Deletable[K]] | UnionRefBases,
        key: K,
    ) -> None:
        """Initialize mapping remove command.

        Args:
            ref: Mapping reference to remove key from
            key: Key to remove
        """
        self.ref = cast("ViewRef[view_capabilities.Deletable[K]]", ref)
        self.key = key
        self.children = (cast("ViewRef[view_capabilities.Deletable[K]]", ref),)

    def execute(self, context: Context) -> None:
        """Execute remove command.

        Args:
            context: Execution context with transaction

        Returns:
            None

        Raises:
            KeyError: If key not in mapping
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Remove through view
        if not isinstance(view, view_capabilities.Deletable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Deletable protocol."
            )

        del view[self.key]
        return None

    def __repr__(self) -> str:
        return f"MappingRemoveCmd({self.ref!r}, {self.key!r})"
