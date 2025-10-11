# tree/registry.py
"""View registry for mapping between structures, container types, component types, and view classes.

This module provides the ViewRegistry class that manages bidirectional mappings
between container structure IDs, container types, navigation component types,
and view classes.

The registry handles two distinct use cases:
1. Container creation: When storing a value, which view should handle it?
2. Navigation: When navigating with a component, which view can handle that component type?

Users can create completely custom container and component types with domain-specific
logic that have no connection to Python built-in types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .view import DictView, ListView


if TYPE_CHECKING:
    from .view import BaseView

__all__ = [
    "ComponentType",
    "ContainerType",
    "ViewRegistry",
]


class ContainerConstructor:
    """Base class for container types that views can handle.

    Container types represent what kind of data structure a view creates/manages.
    Views register with container types to indicate what they can store.

    Example:
        ```python
        class DictContainer(ContainerType):
            pass


        class ListContainer(ContainerType):
            pass


        class DocumentContainer(ContainerType):
            pass  # Custom container with domain-specific logic
        ```
    """

    pass


type ContainerType = type[dict | list | tuple | ContainerConstructor]


class ComponentConstructor:
    """Base class for component types that can be used in navigation.

    Component types represent what kind of keys/navigation elements a view can handle.
    Views register with component types to indicate what navigation they support.

    Example:
        ```python
        class StringComponent(ComponentType):
            pass


        class IntegerComponent(ComponentType):
            pass


        class NodeIDComponent(ComponentType):
            # Custom navigation component for graph traversal
            pass
        ```
    """

    pass


type ComponentType = type[int | str | ComponentConstructor]


class ViewRegistry:
    """Central registry for view mappings.

    Manages mappings between:
    - Structure IDs ↔ View Classes (for resolving existing containers)
    - Container Types ↔ View Classes (for creating new containers from values)
    - Component Types ↔ View Classes (for navigation with different key types)

    No fallback logic - all mappings must be explicitly registered.
    """

    def __init__(self) -> None:
        """Initialize registry with native views."""
        # =========================================================================
        # INTERNAL STORAGE
        # =========================================================================

        # Structure ID → View Class (for resolving existing containers)
        self._structure_to_view: dict[int, type[BaseView]] = {}

        # Container Type → View Class (for creating containers from values)
        self._container_type_to_view: dict[ContainerType, type[BaseView]] = {}

        # Component Type → List[View Classes] (for navigation - multiple views can handle same component type)
        self._component_type_to_views: dict[ComponentType, list[type[BaseView]]] = {}

        # Reverse mappings
        self._view_to_structure: dict[type[BaseView], int] = {}
        self._view_to_container_type: dict[type[BaseView], ContainerType] = {}
        self._view_to_component_types: dict[type[BaseView], set[ComponentType]] = {}

        # Track registered views for validation
        self._registered_views: set[type[BaseView]] = set()

        # =========================================================================
        # REGISTER BUILTIN VIEWS
        # =========================================================================

        # Register builtin views
        self.register_views(
            {
                # Registering DictView and ListView with their structure IDs and types
                # These are the default views for dict and list containers
                DictView: (1, dict, str),
                ListView: (2, list, int),
            }
        )

    def register_view(
        self,
        view_class: type[BaseView],
        structure_id: int,
        container_type: ContainerType,
        component_types: ComponentType | list[ComponentType],
    ) -> None:
        """Register a view with its structure ID, container type, and supported component types.

        Args:
            view_class: The view class to register
            structure_id: Unique container structure ID this view handles
            container_type: Container type this view creates/manages
            component_types: Component type(s) this view can navigate with

        Raises:
            ValueError: If structure_id already registered or other conflicts detected

        Example:
            ```python
            # DictView handles DictContainer and navigates with StringComponent
            registry.register_view(
                DictView,
                structure_id=1,
                container_type=DictContainer,
                component_types=StringComponent,
            )

            # ListView handles ListContainer and navigates with IntegerComponent
            registry.register_view(
                ListView,
                structure_id=2,
                container_type=ListContainer,
                component_types=IntegerComponent,
            )

            # DocumentView handles DocumentContainer but navigates with StringComponent
            registry.register_view(
                DocumentView,
                structure_id=100,
                container_type=DocumentContainer,
                component_types=StringComponent,
            )

            # GraphView can navigate with both StringComponent and NodeIDComponent
            registry.register_view(
                GraphView,
                structure_id=101,
                container_type=GraphContainer,
                component_types=[StringComponent, NodeIDComponent],
            )
            ```
        """
        # Normalize component_types to list
        if not isinstance(component_types, list):
            component_types = [component_types]

        # Validation: Check for structure ID conflicts
        if structure_id in self._structure_to_view:
            existing_view = self._structure_to_view[structure_id]
            if existing_view != view_class:
                raise ValueError(
                    f"Structure ID {structure_id} already registered to {existing_view.__name__}, "
                    f"cannot register to {view_class.__name__}"
                )

        # Validation: Check for container type conflicts
        if container_type in self._container_type_to_view:
            existing_view = self._container_type_to_view[container_type]
            if existing_view != view_class:
                raise ValueError(
                    f"Container type {container_type} already registered to {existing_view.__name__}, "
                    f"cannot register to {view_class.__name__}"
                )

        # Validation: Check if view already registered with different structure ID
        if view_class in self._view_to_structure:
            existing_structure = self._view_to_structure[view_class]
            if existing_structure != structure_id:
                raise ValueError(
                    f"View {view_class.__name__} already registered with structure ID {existing_structure}, "
                    f"cannot re-register with structure ID {structure_id}"
                )

        # Validation: Check if view already registered with different container type
        if view_class in self._view_to_container_type:
            existing_container_type = self._view_to_container_type[view_class]
            if existing_container_type != container_type:
                raise ValueError(
                    f"View {view_class.__name__} already registered with container type {existing_container_type}, "
                    f"cannot re-register with container type {container_type}"
                )

        # Register forward mappings
        self._structure_to_view[structure_id] = view_class
        self._container_type_to_view[container_type] = view_class

        # Register component type mappings (multiple views can handle same component type)
        for comp_type in component_types:
            if comp_type not in self._component_type_to_views:
                self._component_type_to_views[comp_type] = []
            if view_class not in self._component_type_to_views[comp_type]:
                self._component_type_to_views[comp_type].append(view_class)

        # Register reverse mappings
        self._view_to_structure[view_class] = structure_id
        self._view_to_container_type[view_class] = container_type
        self._view_to_component_types[view_class] = set(component_types)

        # Track registered views
        self._registered_views.add(view_class)

    def register_views(
        self,
        mappings: dict[
            type[BaseView],
            tuple[int, ContainerType, ComponentType | list[ComponentType]],
        ],
    ) -> None:
        """Batch register multiple views.

        Args:
            mappings: Dict of {view_class: (structure_id, container_type, component_types)}

        Example:
            ```python
            registry.register_views(
                {
                    DictView: (1, DictContainer, StringComponent),
                    ListView: (2, ListContainer, IntegerComponent),
                    DocumentView: (100, DocumentContainer, StringComponent),
                    GraphView: (101, GraphContainer, [StringComponent, NodeIDComponent]),
                }
            )
            ```
        """
        for view_class, (structure_id, container_type, component_types) in mappings.items():
            self.register_view(view_class, structure_id, container_type, component_types)

    # =========================================================================
    # LOOKUP METHODS - Forward Mappings
    # =========================================================================

    def get_view_for_structure(self, structure_id: int) -> type[BaseView]:
        """Get view class for structure ID.

        Used when resolving existing containers from storage.

        Args:
            structure_id: Container structure ID

        Returns:
            View class that handles this structure ID

        Raises:
            ValueError: If structure ID not registered
        """
        view_class = self._structure_to_view.get(structure_id)
        if view_class is None:
            raise ValueError(f"No view registered for structure ID {structure_id}")
        return view_class

    def get_view_for_container_type(self, container_type: ContainerType) -> type[BaseView]:
        """Get view class for container type.

        Used when creating new containers from values.

        Args:
            container_type: Container type class

        Returns:
            View class that handles this container type

        Raises:
            ValueError: If container type not registered
        """
        view_class = self._container_type_to_view.get(container_type)
        if view_class is None:
            raise ValueError(f"No view registered for container type {container_type}")
        return view_class

    def get_views_for_component_type(self, component_type: ComponentType) -> list[type[BaseView]]:
        """Get view classes that can handle a component type.

        Used during navigation to find views that can handle specific key types.
        Returns list because multiple views might handle the same component type.

        Args:
            component_type: Component/key type class

        Returns:
            List of view classes that can handle this component type

        Raises:
            ValueError: If component type not supported by any view
        """
        view_classes = self._component_type_to_views.get(component_type, [])
        if not view_classes:
            raise ValueError(f"No views registered for component type {component_type}")
        return view_classes.copy()  # Return copy to prevent external modification

    def get_primary_view_for_component_type(self, component_type: ComponentType) -> type[BaseView]:
        """Get the primary (first registered) view for a component type.

        Convenience method for when you need just one view for a component type.

        Args:
            component_type: Component/key type class

        Returns:
            Primary view class for this component type
        """
        views = self.get_views_for_component_type(component_type)
        return views[0]

    # =========================================================================
    # LOOKUP METHODS - Reverse Mappings
    # =========================================================================

    def get_structure_for_view(self, view_class: type[BaseView]) -> int:
        """Get structure ID for view class."""
        structure_id = self._view_to_structure.get(view_class)
        if structure_id is None:
            raise ValueError(f"View class {view_class.__name__} not registered")
        return structure_id

    def get_container_type_for_view(self, view_class: type[BaseView]) -> ContainerType:
        """Get container type for view class."""
        container_type = self._view_to_container_type.get(view_class)
        if container_type is None:
            raise ValueError(f"View class {view_class.__name__} not registered")
        return container_type

    def get_component_types_for_view(self, view_class: type[BaseView]) -> set[ComponentType]:
        """Get supported component types for view class."""
        component_types = self._view_to_component_types.get(view_class)
        if component_types is None:
            raise ValueError(f"View class {view_class.__name__} not registered")
        return component_types.copy()  # Return copy to prevent external modification

    # =========================================================================
    # VALIDATION AND INTROSPECTION
    # =========================================================================

    def is_registered_structure(self, structure_id: int) -> bool:
        """Check if structure ID is registered."""
        return structure_id in self._structure_to_view

    def is_registered_container_type(self, container_type: ContainerType) -> bool:
        """Check if container type is registered."""
        return container_type in self._container_type_to_view

    def is_registered_component_type(self, component_type: ComponentType) -> bool:
        """Check if component type is supported by any view."""
        return component_type in self._component_type_to_views

    def is_registered_view(self, view_class: type[BaseView]) -> bool:
        """Check if view class is registered."""
        return view_class in self._registered_views

    def get_registered_structures(self) -> dict[int, type[BaseView]]:
        """Get copy of structure ID → view class mappings."""
        return self._structure_to_view.copy()

    def get_registered_container_types(self) -> dict[ContainerType, type[BaseView]]:
        """Get copy of container type → view class mappings."""
        return self._container_type_to_view.copy()

    def get_registered_component_types(self) -> dict[ComponentType, list[type[BaseView]]]:
        """Get copy of component type → view classes mappings."""
        return {k: v.copy() for k, v in self._component_type_to_views.items()}

    def get_registered_views(self) -> set[type[BaseView]]:
        """Get copy of all registered view classes."""
        return self._registered_views.copy()

    # =========================================================================
    # DEBUGGING AND REPRESENTATION
    # =========================================================================

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"ViewRegistry("
            f"views={len(self._registered_views)}, "
            f"structures={len(self._structure_to_view)}, "
            f"container_types={len(self._container_type_to_view)}, "
            f"component_types={len(self._component_type_to_views)})"
        )

    def debug_info(self) -> str:
        """Detailed debug information about registry state."""
        lines = ["ViewRegistry Debug Info:"]
        lines.append(f"  Registered Views: {len(self._registered_views)}")

        lines.append("  Structure ID → View:")
        for struct_id, view_class in sorted(self._structure_to_view.items()):
            lines.append(f"    {struct_id} → {view_class.__name__}")

        lines.append("  Container Type → View:")
        for cont_type, view_class in self._container_type_to_view.items():
            lines.append(f"    {cont_type} → {view_class.__name__}")

        lines.append("  Component Type → Views:")
        for comp_type, view_classes in self._component_type_to_views.items():
            view_names = [v.__name__ for v in view_classes]
            lines.append(f"    {comp_type} → {view_names}")

        return "\n".join(lines)
