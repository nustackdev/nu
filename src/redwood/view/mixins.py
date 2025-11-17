"""View mixins for composing custom view behaviors.

This module provides reusable mixins that encapsulate common view patterns:
- Metadata-based children counting
- Live children counting
- Child navigation with address normalization
- Nested container extraction (get)
- Nested container population (set)
"""

from __future__ import annotations

from abc import abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, cast

from redwood.loc import key as key_
from redwood.tree import Container, ContainerStructure, NodeType
from redwood.types import Convertible, Empty, Initializable, is_empty


if TYPE_CHECKING:
    from redwood.view import View, ViewRegistry


__all__ = [
    "ChildNavigationMixin",
    "ChildNestedGetMixin",
    "ChildNestedSetMixin",
    "LiveChildrenCountMixin",
    "MetadataBasedChildrenCountMixin",
]

logger = getLogger(__name__)


class MetadataBasedChildrenCountMixin:
    """Mixin for views that track children count via metadata.

    Provides __len__ implementation and helper methods for maintaining
    the "__len__" metadata field efficiently.

    Type Parameters:
        A: Address/key type for children
        V: Value type for children

    Example:
        >>> class MyView(MetadataBasedChildrenCountMixin[str, int], View):
        ...     def add_item(self, key: str, value: int):
        ...         self.container.set_child_primitive(key, value)
        ...         self._increment_length()
    """

    container: Container

    def __len__(self) -> int:
        """Get number of children.

        Returns:
            Number of children tracked in metadata
        """
        length = cast("int", self.container.get_metadata("__len__", default=0))
        return int(length) if length is not None else 0

    def _increment_length(self) -> None:
        """Increment children count by 1."""
        current_len = cast("int", self.container.get_metadata("__len__", default=0))
        self.container.set_metadata(
            "__len__", int(current_len) + 1 if current_len is not None else 1
        )

    def _decrement_length(self) -> None:
        """Decrement children count by 1."""
        current_len = cast("int", self.container.get_metadata("__len__", default=0))
        if current_len and int(current_len) > 0:
            self.container.set_metadata("__len__", int(current_len) - 1)

    def _set_length(self, n: int) -> None:
        """Set children count to specific value.

        Args:
            n: New length value
        """
        self.container.set_metadata("__len__", n)

    def _update_count(self) -> None:
        """Update length metadata by counting direct children.

        Iterates over all direct children and updates the __len__ metadata.
        Useful for ensuring consistency or recovering from operations that
        bypass the increment/decrement helpers.
        """
        count = sum(1 for _ in self.container.list_child_keys())
        self._set_length(count)


class LiveChildrenCountMixin:
    """Mixin for views that count children on-the-fly.

    Provides __len__ implementation that counts children in real-time
    without relying on metadata. Less efficient but always accurate.

    Type Parameters:
        A: Address/key type for children
        V: Value type for children

    Example:
        >>> class MyView(LiveChildrenCountMixin[str, int], View):
        ...     # No need to track length manually
        ...     def add_item(self, key: str, value: int):
        ...         self.container.set_child_primitive(key, value)
    """

    container: Container

    def __len__(self) -> int:
        """Get number of children by counting them.

        Returns:
            Number of children (counted on each call)
        """
        return sum(1 for _ in self.container.list_child_keys())


class ChildNavigationMixin[A]:
    """Mixin for typed child view access with address normalization.

    Provides open_child() method that creates a child view with proper
    address normalization. Subclasses implement address_normalization()
    to customize address handling (e.g., negative index support).

    Type Parameters:
        A: Address/key type for children
        V: Value type for children

    Example:
        >>> class MyListView(ChildNavigationMixin[int, str], View):
        ...     def address_normalization(self, address: int) -> int:
        ...         # Support negative indices
        ...         if address < 0:
        ...             return len(self) + address
        ...         return address
    """

    container: Container
    registry: ViewRegistry

    @abstractmethod
    def address_normalization(self, address: A) -> str | int:
        """Normalize address before accessing child.

        Subclasses implement this to handle view-specific address logic
        (e.g., negative indices for ListView, passthrough for DictView).

        Args:
            address: Raw address from user

        Returns:
            Normalized address for storage access

        Raises:
            IndexError, KeyError: If address invalid
        """
        ...

    def open_child[ViewT: View](self, address: A, view: type[ViewT]) -> ViewT:
        """Open child view at address.

        Args:
            address: Child container address (will be normalized)
            view: View class for child

        Returns:
            View instance for child container

        Raises:
            IndexError, KeyError: If address invalid after normalization
        """
        normalized_address = self.address_normalization(address)
        child_container = Container.create(
            key_.join_segment(self.container.path, normalized_address),
            self.container.ctx,
            view.get_structure(),
            view.get_protocol(),
        )
        return view(child_container, self.registry)


class ChildNestedGetMixin:
    """Mixin for getting child values with automatic container extraction.

    Provides methods to get child values that automatically extract nested
    containers using the registry. Primitives are returned directly.

    Type Parameters:
        A: Address/key type for children
        V: Value type for children

    Example:
        >>> class MyView(ChildNestedGetMixin[str, dict], View):
        ...     def get_item(self, key: str) -> dict:
        ...         return self._get_child_value(key)
    """

    container: Container
    registry: ViewRegistry

    def _get_child_value(self, key: key_.KeySegment) -> object | Empty:
        """Get child value, auto-extracting containers.

        Helper for subclasses implementing dict-like or list-like access.
        Automatically extracts nested containers using registry.

        Args:
            key: Child key

        Returns:
            Primitive value or extracted container contents

        Raises:
            KeyError: If child doesn't exist
        """
        child_type = self.container.get_child_type(key)

        if child_type == NodeType.NOT_FOUND:
            raise KeyError(key)

        if child_type == NodeType.PRIMITIVE:
            value = self.container.get_child_primitive(key)
            if is_empty(value):
                raise KeyError(key)
            return value

        # Child is container - extract it
        return self._extract_child_container(key)

    def _extract_child_container(self, key: key_.KeySegment) -> object:
        """Extract child container contents using registry.

        Args:
            key: Child key

        Returns:
            Extracted Python value

        Raises:
            ValueError: If child has no structure ID
            TypeError: If child view doesn't support extraction
        """
        # Get child container
        child_path = (*self.container.path, key)
        child_container = Container(ctx=self.container.ctx, path=child_path)

        # Get structure ID
        child_info = child_container.info()
        if child_info.structure is None:
            logger.error(
                "Child container has no structure ID",
                extra={"parent_path": self.container.path, "child_key": key},
            )
            raise ValueError(f"Child container '{key}' has no structure ID")

        # Find appropriate view
        view_class = self.registry.get_view_for_structure(child_info.structure)
        child_view = view_class(container=child_container, registry=self.registry)

        # Extract if supported
        if not isinstance(child_view, Convertible):
            logger.error(
                "Child view does not support extraction",
                extra={
                    "parent_path": self.container.path,
                    "child_key": key,
                    "view_class": view_class.__name__,
                },
            )
            raise TypeError(f"Child view {view_class.__name__} does not support extraction")

        logger.debug(
            "Extracting child container",
            extra={
                "parent_path": self.container.path,
                "child_key": key,
                "view_class": view_class.__name__,
                "structure": child_info.structure,
            },
        )
        return child_view.extract()


class ChildNestedSetMixin:
    """Mixin for setting child values with automatic container population.

    Provides methods to set child values that automatically populate nested
    containers using the registry. Primitives are stored directly.

    Type Parameters:
        A: Address/key type for children
        V: Value type for children

    Example:
        >>> class MyView(ChildNestedSetMixin[str, dict], View):
        ...     def set_item(self, key: str, value: dict):
        ...         self._set_child_value(key, value)
    """

    container: Container
    registry: ViewRegistry

    def _set_child_value(self, key: key_.KeySegment, value: object) -> None:
        """Set child value, auto-creating containers for complex types.

        Helper for subclasses implementing dict-like or list-like mutation.
        Automatically populates nested containers using registry.

        Args:
            key: Child key
            value: Value to store (primitive or container)
        """
        if self.registry.is_container_type(value):
            # Value is a container type - populate it
            self._populate_child_container(key, value)
        else:
            # Primitive value - store directly
            from redwood.types import Value

            self.container.set_child_primitive(key, cast("Value", value))

    def _populate_child_container(self, key: key_.KeySegment, value: object) -> None:
        """Populate child container from Python value using registry.

        Args:
            key: Child key
            value: Container value to store

        Raises:
            TypeError: If child view doesn't support initialization
        """
        # Get view class and structure for this value type
        value_type = type(value)
        view_class = self.registry.get_view_for_type(value_type)
        structure_id = view_class.get_structure()
        protocol_hints = view_class.get_protocol()

        logger.debug(
            "Populating child container",
            extra={
                "parent_path": self.container.path,
                "child_key": key,
                "value_type": value_type.__name__,
                "view_class": view_class.__name__,
                "structure": structure_id,
            },
        )

        # Create child container
        child_container = self.container.create_child_container(
            key=key,
            structure=ContainerStructure(structure_id),
            protocol=protocol_hints,
        )

        # Create view and populate
        child_view = view_class(container=child_container, registry=self.registry)

        # Store if supported
        if not isinstance(child_view, Initializable):
            logger.error(
                "Child view does not support initialization",
                extra={
                    "parent_path": self.container.path,
                    "child_key": key,
                    "view_class": view_class.__name__,
                },
            )
            raise TypeError(f"Child view {view_class.__name__} does not support initialization")

        child_view.store(value)
