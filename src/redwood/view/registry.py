"""View registry for mapping between structures, container types and view classes.

This module provides the ViewRegistry class that manages bidirectional mappings
between container structure IDs, container types and view classes.

Users can create completely custom container and component types with domain-specific
logic that have no connection to Python built-in types.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, NamedTuple

from redwood.tree import ContainerStructure

from .exceptions import RegistryError


if TYPE_CHECKING:
    from redwood.tree import ContainerStructure

    from .view import View

__all__ = [
    "ViewRegistration",
    "ViewRegistry",
]


logger = getLogger(__name__)


class ViewRegistration(NamedTuple):
    """Registration entry mapping types to views."""

    view_class: type[View]
    structure_id: int
    container_type: type | None = None


class ViewRegistry:
    """Maps between Python types and View classes.

    Provides bidirectional mapping:
    - Python type → View (for writing/storing)
    - Structure ID → View (for reading/extracting)

    Example:
        >>> registry = ViewRegistry()
        >>> registry.register(DictView, structure_id=1, container_type=dict)
        >>> registry.register(ListView, structure_id=2, container_type=list)
        >>> # Writing: dict → DictView
        >>> view_class = registry.get_view_for_type(dict)
        >>> # Reading: structure=1 → DictView
        >>> view_class = registry.get_view_for_structure(1)
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._structure_to_view: dict[ContainerStructure, type[View]] = {}
        self._type_to_registration: dict[type, ViewRegistration] = {}

    def register(
        self,
        view_class: type[View],
    ) -> None:
        """Register a view class.

        Args:
            view_class: View class to register
        Raises:
            RegistryError: If structure_id or container_type already registered
        """
        structure_id: ContainerStructure = view_class.get_structure()
        container_type: type | None = view_class.get_container_cls()

        # Register structure ID → view
        if structure_id in self._structure_to_view:
            existing = self._structure_to_view[structure_id]
            logger.error(
                "Structure ID already registered",
                extra={
                    "structure_id": structure_id,
                    "existing_view": existing.__name__,
                    "attempted_view": view_class.__name__,
                },
            )
            raise RegistryError(
                f"Structure ID {structure_id} already registered to {existing.__name__}"
            )
        self._structure_to_view[structure_id] = view_class

        # Register container type → registration
        if container_type is not None:
            if container_type in self._type_to_registration:
                existing = self._type_to_registration[container_type]
                logger.error(
                    "Container type already registered",
                    extra={
                        "container_type": container_type.__name__,
                        "existing_view": existing.view_class.__name__,
                        "attempted_view": view_class.__name__,
                    },
                )
                raise RegistryError(
                    f"Container type {container_type.__name__} already registered to "
                    f"{existing.view_class.__name__}"
                )
            registration = ViewRegistration(
                view_class=view_class,
                structure_id=structure_id,
                container_type=container_type,
            )
            self._type_to_registration[container_type] = registration

        logger.debug(
            "View registered",
            extra={
                "view_class": view_class.__name__,
                "structure_id": structure_id,
                "container_type": container_type.__name__ if container_type else None,
            },
        )

    def get_view_for_structure(self, structure_id: ContainerStructure) -> type[View]:
        """Get view class for structure ID (reading).

        Args:
            structure_id: Structure ID from storage

        Returns:
            View class for this structure

        Raises:
            RegistryError: If structure_id not registered
        """
        if structure_id not in self._structure_to_view:
            logger.warning(
                "No view registered for structure ID",
                extra={"structure_id": structure_id},
            )
            raise RegistryError(f"No view registered for structure ID {structure_id}")

        view_class = self._structure_to_view[structure_id]
        logger.debug(
            "View lookup by structure",
            extra={"structure_id": structure_id, "view_class": view_class.__name__},
        )
        return view_class

    def get_view_for_type(self, container_type: type) -> type[View]:
        """Get view class for Python type (writing).

        Args:
            container_type: Python type (dict, list, etc.)

        Returns:
            View class for this type

        Raises:
            RegistryError: If type not registered
        """
        # Try exact match first
        if container_type in self._type_to_registration:
            view_class = self._type_to_registration[container_type].view_class
            logger.debug(
                "View lookup by type (exact match)",
                extra={
                    "container_type": container_type.__name__,
                    "view_class": view_class.__name__,
                },
            )
            return view_class

        # Try isinstance check for subclasses
        for registered_type, registration in self._type_to_registration.items():
            if isinstance(container_type, type) and issubclass(container_type, registered_type):
                logger.debug(
                    "View lookup by type (subclass match)",
                    extra={
                        "container_type": container_type.__name__,
                        "registered_type": registered_type.__name__,
                        "view_class": registration.view_class.__name__,
                    },
                )
                return registration.view_class

        logger.warning(
            "No view registered for type",
            extra={"container_type": container_type.__name__},
        )
        raise RegistryError(f"No view registered for type {container_type.__name__}")

    def get_structure_for_type(self, container_type: type) -> int:
        """Get structure ID for Python type.

        Args:
            container_type: Python type

        Returns:
            Structure ID for this type

        Raises:
            RegistryError: If type not registered
        """
        if container_type not in self._type_to_registration:
            raise RegistryError(f"No registration for type {container_type.__name__}")
        return self._type_to_registration[container_type].structure_id

    def is_container_type(self, value: object) -> bool:
        """Check if value matches any registered container type.

        Args:
            value: Value to check

        Returns:
            True if value matches a registered container type
        """
        for container_type in self._type_to_registration:
            if isinstance(value, container_type):
                return True
        return False
