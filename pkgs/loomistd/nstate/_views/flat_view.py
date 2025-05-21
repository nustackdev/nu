"""
FlatView implementation for the state management system.

This module defines the FlatView class, which provides a dictionary-like
interface for containers implementing the MAPPING and FLAT protocols.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, cast

from .._core.primitive import PrimitiveNode
from .._core.transaction import TransactionContext
from .._exceptions import ContainerProtocolError, ValueTypeError
from .._types import ContainerProtocol, NodeType, PathComponent
from .._utils import is_empty
from .view import BaseView

__all__ = ["FlatView"]


class FlatView(BaseView):
    """
    Flat view for containers implementing the MAPPING and FLAT protocols.

    FlatView provides a dictionary-like interface for interacting with
    containers that can only contain primitive values (not nested containers).
    It supports standard dictionary operations like get, set, keys, values,
    items, as well as conversion to Python dictionaries.

    Example:
        ```python
        # Create a flat view
        config = state.at("config").flat_view()

        # Set primitive values
        config.set("theme", "dark")
        config.set("font_size", 14)
        config.set("show_toolbar", True)

        # Get values
        theme = config.get("theme")

        # Check for keys
        if config.has("font_size"):
            print("Font size is configured")

        # Iterate over items
        for key, value in config.items():
            print(f"{key}: {value}")
        ```
    """

    @staticmethod
    def required_protocols() -> ContainerProtocol:
        """
        Get the protocols required by this view.

        Returns:
            ContainerProtocol: MAPPING and FLAT protocols
        """
        return ContainerProtocol.MAPPING | ContainerProtocol.FLAT

    def _is_primitive_value(self, value: Any, /) -> bool:
        """
        Check if a value is a primitive value.

        Args:
            value: Value to check

        Returns:
            bool: True if the value is a primitive value
        """
        # Primitive types: None, bool, int, float, str, bytes
        return value is None or isinstance(value, (bool, int, float, str, bytes))

    def get(self, key: PathComponent, /) -> Any:
        """
        Get the value associated with a key.

        Args:
            key: Key to get value for

        Returns:
            Any: Value associated with key, or None if key doesn't exist

        Example:
            ```python
            theme = config.get("theme")
            ```
        """
        # Check if child exists
        if not self.container.has_child(key, tx=self._tx):
            return None

        # Get child node
        child = self.container.get_child(key, tx=self._tx)
        if child is None:
            return None

        # For flat views, only primitive nodes are allowed
        if child.node_type() != NodeType.PRIMITIVE:
            # Container found where primitive expected - treat as error
            raise ValueTypeError(f"Expected primitive value at '{key}', found container")

        # Extract primitive value
        primitive = cast(PrimitiveNode, child)
        value = primitive.get_value(tx=self._tx)
        return None if is_empty(value) else value

    def set(self, key: PathComponent, value: Any, /) -> None:
        """
        Set a value for a key.

        Args:
            key: Key to set value for
            value: Value to associate with key (must be primitive)

        Raises:
            ContainerProtocolError: If container doesn't support mutation
            ValueTypeError: If value is not a primitive value

        Example:
            ```python
            config.set("theme", "dark")
            ```
        """
        with TransactionContext(self.container.backend, tx=self._tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Validate value is primitive
            if not self._is_primitive_value(value):
                raise ValueTypeError(
                    f"FlatView can only store primitive values, got {type(value).__name__}"
                )

            # Create child path
            child_path = self.container.path.join(key)

            # Create primitive node for the value
            primitive = PrimitiveNode(self.container.backend, child_path, tx=transaction)
            primitive.set_value(value, tx=transaction)
            self.container.set_child(key, primitive, tx=transaction)

    def has(self, key: PathComponent, /) -> bool:
        """
        Check if a key exists.

        Args:
            key: Key to check

        Returns:
            bool: True if key exists

        Example:
            ```python
            if config.has("theme"):
                print("Theme is configured")
            ```
        """
        return self.container.has_child(key, tx=self._tx)

    def remove(self, key: PathComponent, /) -> None:
        """
        Remove a key and its associated value.

        Args:
            key: Key to remove

        Raises:
            KeyError: If key doesn't exist
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            config.remove("theme")
            ```
        """
        with TransactionContext(self.container.backend, tx=self._tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Check if key exists
            if not self.container.has_child(key, tx=transaction):
                raise KeyError(f"Key '{key}' not found")

            # Remove the key
            self.container.remove_child(key, tx=transaction)

    def update(self, mapping: Dict[PathComponent, Any], /) -> None:
        """
        Update multiple key-value pairs.

        Args:
            mapping: Dictionary of key-value pairs to update

        Raises:
            ContainerProtocolError: If container doesn't support mutation
            ValueTypeError: If any value is not a primitive value

        Example:
            ```python
            config.update({
                "theme": "dark",
                "font_size": 14,
                "show_toolbar": True
            })
            ```
        """
        with TransactionContext(self.container.backend, tx=self._tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Validate all values are primitive
            for key, value in mapping.items():
                if not self._is_primitive_value(value):
                    raise ValueTypeError(
                        f"FlatView can only store primitive values, "
                        f"got {type(value).__name__} for key '{key}'"
                    )

            # Update all key-value pairs
            for key, value in mapping.items():
                self.set(key, value)

    def values(self) -> List[Any]:
        """
        Get all values in the dictionary.

        Returns:
            List[Any]: List of values

        Example:
            ```python
            all_values = config.values()
            ```
        """
        result = []
        for key in self.keys():
            try:
                value = self.get(key)
                if value is not None:
                    result.append(value)
            except Exception:
                # Skip values that can't be retrieved
                continue
        return result

    def items(self) -> List[Tuple[PathComponent, Any]]:
        """
        Get all key-value pairs.

        Returns:
            List[Tuple[PathComponent, Any]]: List of (key, value) tuples

        Example:
            ```python
            for key, value in config.items():
                print(f"{key}: {value}")
            ```
        """
        result = []
        for key in self.keys():
            try:
                value = self.get(key)
                if value is not None:
                    result.append((key, value))
            except Exception:
                # Skip values that can't be retrieved
                continue
        return result

    def clear(self) -> None:
        """
        Remove all key-value pairs.

        Raises:
            ContainerProtocolError: If container doesn't support mutation

        Example:
            ```python
            config.clear()
            ```
        """
        with TransactionContext(self.container.backend, tx=self._tx) as transaction:
            # Validate container supports mutation
            if not self.container.supports_protocol(ContainerProtocol.MUTABLE):
                raise ContainerProtocolError(
                    f"Container at {self.container.path} does not support mutation"
                )

            # Clear the container
            self.container.clear(tx=transaction)

    def to_dict(self) -> Dict[PathComponent, Any]:
        """
        Convert to a Python dictionary.

        Returns:
            Dict[PathComponent, Any]: Dictionary representation

        Example:
            ```python
            config_dict = config.to_dict()
            ```
        """
        result = {}
        for key, value in self.items():
            result[key] = value
        return result
