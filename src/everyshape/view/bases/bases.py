"""View bases for composing custom view behaviors.

This module provides reusable bases that encapsulate common view patterns:
- Metadata-based children counting
- Live children counting
- Child navigation with address normalization
- Nested container extraction (get)
- Nested container population (set)
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, cast

from everyshape.container import Container, ContainerStructure, NodeType, node_ops
from everyshape.typing import Empty, Value, is_empty


if TYPE_CHECKING:
    from everyshape.container.types import NodeInfo
    from everyshape.loc import site as site_
    from everyshape.view import View, ViewRegistry


__all__ = [
    "ChildNavigationBase",
    "ChildNestedGetBase",
    "ChildNestedSetBase",
    "LiveChildrenCountBase",
    "MetadataBasedChildrenCountBase",
]

logger = getLogger(__name__)


class MetadataBasedChildrenCountBase:
    """Base for views that track children count via metadata.

    Provides __len__ implementation and helper methods for maintaining
    the "__len__" metadata field efficiently.

    Type Parameters:
        A: Address type for children
        V: Value type for children

    Example:
        >>> class MyView(MetadataBasedChildrenCountBase[str, int], View):
        ...     def add_item(self, address: str, value: int):
        ...         self.container.put_child_primitive(address, value)
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
        self.container.put_metadata("__len__", int(current_len) + 1)

    def _decrement_length(self) -> None:
        """Decrement children count by 1."""
        current_len = cast("int", self.container.get_metadata("__len__", default=0))
        if current_len and int(current_len) > 0:
            self.container.put_metadata("__len__", int(current_len) - 1)

    def _set_length(self, n: int) -> None:
        """Set children count to specific value.

        Args:
            n: New length value
        """
        self.container.put_metadata("__len__", n)

    def _update_count(self) -> None:
        """Update length metadata by counting direct children.

        Iterates over all direct children and updates the __len__ metadata.
        Useful for ensuring consistency or recovering from operations that
        bypass the increment/decrement helpers.
        """
        count = sum(1 for _ in self.container.iter_child_keys())
        self._set_length(count)


class LiveChildrenCountBase:
    """Base for views that count children on-the-fly.

    Provides __len__ implementation that counts children in real-time
    without relying on metadata. Less efficient but always accurate.

    Type Parameters:
        A: Address type for children
        V: Value type for children

    Example:
        >>> class MyView(LiveChildrenCountBase[str, int], View):
        ...     # No need to track length manually
        ...     def add_item(self, address: str, value: int):
        ...         self.container.put_child_primitive(address, value)
    """

    container: Container

    def __len__(self) -> int:
        """Get number of children by counting them.

        Returns:
            Number of children (counted on each call)
        """
        return sum(1 for _ in self.container.iter_child_keys())


class AddressMappingBase[A]:
    """Base for converting view-level addresses to container keys.

    Provides a single hook normalize_address() that defines how a view's
    address type A maps onto the underlying Container key space.

    Type Parameters:
        A: Address type for children at the view level
    """

    container: Container

    def normalize_address(self, address: A) -> site_.SiteSegment:
        """Normalize view address to a storage key."""
        raise NotImplementedError


class ChildNavigationBase[A](AddressMappingBase[A]):
    """Base for typed child view access with address normalization.

    Provides open_child() method that creates a child view with proper
    address normalization. Subclasses implement normalize_address()
    to customize address handling (e.g., negative index support).

    Type Parameters:
        A: Address type for children
        V: Value type for children

    Example:
        >>> class MyListView(ChildNavigationBase[int, str], View):
        ...     def normalize_address(self, address: int) -> int:
        ...         # Support negative indices
        ...         if address < 0:
        ...             return len(self) + address
        ...         return address
    """

    container: Container
    registry: ViewRegistry

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
        normalized_address = self.normalize_address(address)
        child_container = Container.create(
            (*self.container.site, normalized_address),
            self.container.ctx,
            view.get_structure(),
            view.get_protocol(),
        )
        return view(child_container, self.registry)


class ChildNestedGetBase:
    """Base for getting child values with automatic container extraction.

    Provides methods to get child values that automatically extract nested
    containers using the registry. Primitives are returned directly.

    Type Parameters:
        A: Address type for children
        V: Value type for children

    Example:
        >>> class MyView(ChildNestedGetBase[str, dict], View):
        ...     def get_item(self, address: str) -> dict:
        ...         return self._get_child_value(address)
    """

    container: Container
    registry: ViewRegistry

    def _get_child_value(
        self,
        address: site_.SiteSegment,
        *,
        node_info: NodeInfo | None = None,
    ) -> object | Empty:
        """Get child value, auto-extracting containers.

        Helper for subclasses implementing dict-like or list-like access.
        Automatically extracts nested containers using registry.

        Args:
            address: Child address
            node_info: Pre-fetched node info to avoid redundant storage read

        Returns:
            Primitive value or extracted container contents

        Raises:
            KeyError: If child doesn't exist
        """
        # Use pre-fetched info or fetch it
        if node_info is None:
            child_site = (*self.container.site, address)
            node_info = node_ops.get_node_info(child_site, self.container.ctx)

        if not node_info.exists or node_info.node_type == NodeType.NOT_FOUND:
            raise KeyError(address)

        if node_info.node_type == NodeType.PRIMITIVE:
            # Primitive value is already in node_info
            if is_empty(node_info.primitive_value):
                raise KeyError(address)
            return node_info.primitive_value

        # Child is container - extract it (pass info to avoid re-read)
        return self._extract_child_container(address, node_info=node_info)

    def _extract_child_container(
        self,
        address: site_.SiteSegment,
        *,
        node_info: NodeInfo | None = None,
    ) -> object:
        """Extract child container contents using registry.

        Args:
            address: Child address
            node_info: Pre-fetched node info to avoid redundant storage read

        Returns:
            Extracted Python value

        Raises:
            ValueError: If child has no structure ID
            TypeError: If child view doesn't support extraction
        """
        from everyshape.typing.view import Convertible

        # Get child container
        child_site = (*self.container.site, address)
        child_container = Container(ctx=self.container.ctx, site=child_site)

        # Use pre-fetched info or get it
        if node_info is None:
            child_info = child_container.info()
        else:
            child_info = node_info

        if child_info.structure is None:
            logger.error(
                "Child container has no structure ID",
                extra={"parent_site": self.container.site, "child_address": address},
            )
            raise ValueError(f"Child container '{address}' has no structure ID")

        # Find appropriate view
        view_class = self.registry.get_view_for_structure(child_info.structure)
        child_view = view_class(container=child_container, registry=self.registry)

        # Extract if supported
        if not isinstance(child_view, Convertible):
            logger.error(
                "Child view does not support extraction",
                extra={
                    "parent_site": self.container.site,
                    "child_address": address,
                    "view_class": view_class.__name__,
                },
            )
            raise TypeError(f"Child view {view_class.__name__} does not support extraction")

        logger.debug(
            "Extracting child container",
            extra={
                "parent_site": self.container.site,
                "child_address": address,
                "view_class": view_class.__name__,
                "structure": child_info.structure,
            },
        )
        return child_view.extract()


class ChildNestedSetBase:
    """Base for setting child values with automatic container population.

    Provides methods to set child values that automatically populate nested
    containers using the registry. Primitives are stored directly.

    Type Parameters:
        A: Address type for children
        V: Value type for children

    Example:
        >>> class MyView(ChildNestedSetBase[str, dict], View):
        ...     def set_item(self, address: str, value: dict):
        ...         self._set_child_value(address, value)
    """

    container: Container
    registry: ViewRegistry

    def _set_child_value(self, address: site_.SiteSegment, value: object) -> None:
        """Set child value, auto-creating containers for complex types.

        Helper for subclasses implementing dict-like or list-like mutation.
        Automatically populates nested containers using registry.

        Args:
            address: Child address
            value: Value to store (primitive or container)
        """
        if self.registry.is_container_type(value):
            # Value is a container type - populate it
            self._populate_child_container(address, value)
        else:
            # Primitive value - store directly
            self.container.put_child_primitive(address, cast("Value", value))

    def _populate_child_container(self, address: site_.SiteSegment, value: object) -> None:
        """Populate child container from Python value using registry.

        Args:
            address: Child address
            value: Container value to store

        Raises:
            TypeError: If child view doesn't support initialization
        """
        from everyshape.typing.view import Initializable

        # Get view class and structure for this value type
        value_type = type(value)
        view_class = self.registry.get_view_for_type(value_type)
        structure_id = view_class.get_structure()
        protocol_hints = view_class.get_protocol()

        logger.debug(
            "Populating child container",
            extra={
                "parent_site": self.container.site,
                "child_address": address,
                "value_type": value_type.__name__,
                "view_class": view_class.__name__,
                "structure": structure_id,
            },
        )

        # Create child container
        child_container = self.container.create_child_container(
            address,
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
                    "parent_site": self.container.site,
                    "child_address": address,
                    "view_class": view_class.__name__,
                },
            )
            raise TypeError(f"Child view {view_class.__name__} does not support initialization")

        child_view.store(value)
