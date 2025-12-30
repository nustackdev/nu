"""Slot implementations for Shape system.

This module provides concrete slot types that create refs:
- ValueSlot: creates ValueRef for primitive values
- MappingSlot / MutableMappingSlot: creates MappingRef / MutableMappingRef for dict-like collections
- SequenceSlot / MutableSequenceSlot: creates SequenceRef / MutableSequenceRef for list-like collections
- SetSlot / MutableSetSlot: creates SetRef / MutableSetRef for set-like collections
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.shape import Slot
from everyshape.term.refs import (
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    SequenceRef,
    SetRef,
    ValueRef,
)


if TYPE_CHECKING:
    from everyshape.shape import Shape
    from everyshape.term import Ref
    from everyshape.types import Value
    from everyshape.view import Mapping, MutableMapping, MutableSequence, MutableSet, Sequence, Set


__all__ = [
    "MappingSlot",
    "MutableMappingSlot",
    "MutableSequenceSlot",
    "MutableSetSlot",
    "SequenceSlot",
    "SetSlot",
    "ValueSlot",
]


class ValueSlot(Slot):
    """Create a value slot for primitive types.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of the value (int, str, float, etc.)

    Returns:
        Slot instance

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)
            balance: ValueRef[float] = ValueSlot(float)
    """

    def __init__(self, value_type: type[Value]) -> None:
        """Init value slot."""
        """Init."""
        super().__init__()
        self.value_type = value_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> ValueRef:
        """Create ValueRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ValueRef instance
        """
        return ValueRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class MappingSlot(Slot):
    """Create a mapping slot for dict-like collections.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type implementing MutableMapping protocol (defaults to DictView)

    Returns:
        Slot instance

    Example:
        from esstd.shapes import MappingSlot, Sequence

        class Market(Shape):
            # Mapping of primitives
            signals: MappingRef[float] = MappingSlot(float)

            # Mapping of shapes
            symbols: MappingRef[SymbolInfo] = MappingSlot(SymbolInfo)

            # Nested: mapping of sequences
            data: MappingRef = MappingSlot(Sequence(float))

        # Access items
        Market.signals["vix"].get()           # ValueRef[float]
        Market.symbols["AAPL"].price.get()    # ShapeRef navigation
        Market.data["timeseries"][0].get()    # Nested collection

    Note:
        The view_type must structurally implement the Mapping protocol
        from everyshape.types.collections.
    """

    def __init__(self, value_type: type[Value], view_type: type[Mapping]) -> None:
        """Init."""
        super().__init__()
        self.value_type = value_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MappingRef:
        """Create MappingRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MappingRef instance
        """
        return MappingRef(
            address=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class SequenceSlot(Slot):
    """Create a sequence slot for list-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type implementing MutableSequence protocol (defaults to ListView)

    Returns:
        Slot instance

    Example:
        from esstd.shapes import SequenceSlot, Mapping

        class Market(Shape):
            # Sequence of primitives
            prices: SequenceRef[float] = SequenceSlot(float)

            # Sequence of shapes
            orders: SequenceRef[Order] = SequenceSlot(Order)

            # Nested: sequence of mappings
            data: SequenceRef = SequenceSlot(Mapping(str))

        # Access items
        Market.prices[0].get()              # ValueRef[float]
        Market.orders[0].id.get()           # ShapeRef navigation
        Market.data[0]["key"].get()         # Nested collection

    Note:
        The view_type must structurally implement the Sequence protocol
        from everyshape.types.collections.
    """

    def __init__(self, item_type: type[Value], view_type: type[Sequence]) -> None:
        """Init."""
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> SequenceRef:
        """Create SequenceRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            SequenceRef instance
        """
        return SequenceRef(
            address=self.name,
            item_type=self.item_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class MutableMappingSlot(Slot):
    """Create a mutable mapping slot for dict-like collections.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: View type implementing MutableMapping protocol

    Returns:
        Slot instance

    Example:
        from esstd.shapes import MutableMappingSlot, Sequence

        class Market(Shape):
            # Mutable mapping of primitives
            signals: MutableMappingRef[float] = MutableMappingSlot(float)

            # Mutable mapping of shapes
            symbols: MutableMappingRef[SymbolInfo] = MutableMappingSlot(SymbolInfo)

            # Nested: mutable mapping of sequences
            data: MutableMappingRef = MutableMappingSlot(Sequence(float))

        # Access items
        Market.signals["vix"].get()           # ValueRef[float]
        Market.symbols["AAPL"].price.get()    # ShapeRef navigation
        Market.data["timeseries"][0].get()    # Nested collection

    Note:
        The view_type must structurally implement the MutableMapping protocol
        from everyshape.types.collections.
    """

    def __init__(self, value_type: type[Value], view_type: type[MutableMapping]) -> None:
        """Init."""
        super().__init__()
        self.value_type = value_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MutableMappingRef:
        """Create MutableMappingRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MutableMappingRef instance
        """
        return MutableMappingRef(
            address=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class MutableSequenceSlot(Slot):
    """Create a mutable sequence slot for list-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: View type implementing MutableSequence protocol

    Returns:
        Slot instance

    Example:
        from esstd.shapes import MutableSequenceSlot, Mapping

        class Market(Shape):
            # Mutable sequence of primitives
            prices: MutableSequenceRef[float] = MutableSequenceSlot(float)

            # Mutable sequence of shapes
            orders: MutableSequenceRef[Order] = MutableSequenceSlot(Order)

            # Nested: mutable sequence of mappings
            data: MutableSequenceRef = MutableSequenceSlot(Mapping(str))

        # Access items
        Market.prices[0].get()              # ValueRef[float]
        Market.orders[0].id.get()           # ShapeRef navigation
        Market.data[0]["key"].get()         # Nested collection

    Note:
        The view_type must structurally implement the MutableSequence protocol
        from everyshape.types.collections.
    """

    def __init__(self, item_type: type[Value], view_type: type[MutableSequence]) -> None:
        """Init."""
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MutableSequenceRef:
        """Create MutableSequenceRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MutableSequenceRef instance
        """
        return MutableSequenceRef(
            address=self.name,
            item_type=self.item_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class SetSlot(Slot):
    """Create a set slot for set-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives only for sets)
        view_type: View type implementing Set protocol

    Returns:
        Slot instance

    Example:
        from esstd.shapes import SetSlot

        class User(Shape):
            # Set of primitives
            tags: SetRef[str] = SetSlot(str)
            permissions: SetRef[int] = SetSlot(int)

        # Access items
        User.tags.contains("admin")  # Check membership

    Note:
        The view_type must structurally implement the Set protocol
        from everyshape.types.collections.
    """

    def __init__(self, item_type: type[Value], view_type: type[Set]) -> None:
        """Init."""
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> SetRef:
        """Create SetRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            SetRef instance
        """
        return SetRef(
            address=self.name,
            item_type=self.item_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


class MutableSetSlot(Slot):
    """Create a mutable set slot for set-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives only for sets)
        view_type: View type implementing MutableSet protocol

    Returns:
        Slot instance

    Example:
        from esstd.shapes import MutableSetSlot

        class User(Shape):
            # Mutable set of primitives
            tags: MutableSetRef[str] = MutableSetSlot(str)
            permissions: MutableSetRef[int] = MutableSetSlot(int)

        # Access items
        User.tags.contains("admin")  # Check membership

    Note:
        The view_type must structurally implement the MutableSet protocol
        from everyshape.types.collections.
    """

    def __init__(self, item_type: type[Value], view_type: type[MutableSet]) -> None:
        """Init."""
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MutableSetRef:
        """Create MutableSetRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MutableSetRef instance
        """
        return MutableSetRef(
            address=self.name,
            item_type=self.item_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
