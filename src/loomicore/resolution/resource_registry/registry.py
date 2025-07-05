from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from loomicore.types import ResourceState

from .exceptions import RegistryError, RegistryKeyError, RegistryStateError
from .logger import logger

if TYPE_CHECKING:
    from loomicore.resource import Resource, ResourceABC
    from loomicore.spec import Spec

__all__ = [
    "ResourceRegistry",
]

ResourceT = TypeVar("ResourceT", bound="ResourceABC")


class ResourceRegistry(Generic[ResourceT]):
    """
    Thread-safe registry managing resource instances and their lifecycle states.

    Primary responsibilities:
    - Maintain unique resource instances based on factory and spec
    - Track and validate resource lifecycle state transitions
    - Provide thread-safe access to resource information

    This registry acts as the source of truth for resource existence and state,
    but delegates relationship management to DependencyManager.
    """

    def __init__(self) -> None:
        self._instances: dict[str, ResourceT] = {}
        self._states: dict[str, ResourceState] = {}
        self._lock = Lock()
        logger.debug("Initialized resource registry")

    def get_resource(
        self,
        spec: "Spec",
    ) -> "Resource | None":
        """
        Retrieve existing resource instance for given factory and spec.
        This is the primary deduplication mechanism - same factory+spec
        should always return the same instance.

        Args:
            spec: Resource specification

        Returns:
            Existing resource instance or None

        Raises:
            RegistryError: If key generation fails
        """
        key = spec.key
        resource = self._instances.get(key, None)

        if resource is not None:
            return self._narrow_to_resource(resource)

        return None

    def add_resource(
        self,
        resource: ResourceT,
    ) -> None:
        """
        Register new resource instance. Should validate the resource
        isn't already registered and initialize its state tracking.

        Args:
            resource: Resource instance to register

        Raises:
            RegistryError: If resource already exists or is invalid
        """
        key = resource.key

        with self._lock:
            if key in self._instances:
                raise RegistryError(f"Resource already exists: '{resource.readable_name}'")

            self._instances[key] = resource
            self._states[key] = ResourceState.CREATED
            logger.debug(f"Registered resource: '{resource.readable_name}'")

    def remove_resource(
        self,
        resource: ResourceT,
    ) -> None:
        """
        Remove resource registration. Should verify the resource is in a valid
        state for removal (not initialized/in use).

        Args:
            resource: Resource to remove

        Raises:
            RegistryError: If resource not found or cannot be removed
        """
        key = resource.key

        with self._lock:
            if key not in self._instances:
                raise RegistryKeyError(f"Resource not found: '{resource.readable_name}'")

            if self._states[key] not in (
                ResourceState.CREATED,
                ResourceState.SHUTDOWN,
                ResourceState.ERROR,
            ):
                raise RegistryStateError(
                    f"Cannot remove resource with state: '{self._states[key]}'"
                )

            self._instances.pop(key)
            self._states.pop(key)
            logger.debug(f"Removed resource: '{resource.readable_name}'")

    def get_resource_state(
        self,
        resource: ResourceT,
    ) -> ResourceState:
        """
        Get current lifecycle state of resource.

        Args:
            resource: Resource to get state for

        Returns:
            Current resource state

        Raises:
            RegistryKeyError: If resource not found
        """
        key = resource.key

        if key not in self._states:
            raise RegistryKeyError(f"Resource not found: '{resource.readable_name}'")

        return self._states[key]

    def set_resource_state(
        self,
        resource: ResourceT,
        state: ResourceState,
    ) -> None:
        """
        Update resource lifecycle state. Enforces valid state transitions
        and maintains thread safety.

        Args:
            resource: Resource to update
            state: New state

        Raises:
            RegistryError: If state transition is invalid
        """
        key = resource.key

        with self._lock:
            if key not in self._states:
                raise RegistryKeyError(f"Resource not found: '{resource.readable_name}'")

            current = self._states[key]
            if not self.is_valid_state_transition(current, state):
                raise RegistryStateError(f"Invalid state transition: '{current}' -> '{state}'")

            self._states[key] = state
            logger.debug(f"Updated resource state: '{resource.readable_name}' -> '{state}'")

    def is_valid_state_transition(
        self,
        current: ResourceState,
        new: ResourceState,
    ) -> bool:
        """Validate state transition."""

        # Implementation of state transition rules
        transitions = {
            ResourceState.CREATED: {ResourceState.INITIALIZING, ResourceState.ERROR},
            ResourceState.INITIALIZING: {ResourceState.INITIALIZED, ResourceState.ERROR},
            ResourceState.INITIALIZED: {ResourceState.SHUTTING_DOWN, ResourceState.ERROR},
            ResourceState.SHUTTING_DOWN: {ResourceState.SHUTDOWN, ResourceState.ERROR},
            ResourceState.SHUTDOWN: {ResourceState.INITIALIZING, ResourceState.ERROR},
            ResourceState.ERROR: set(),
        }
        return new in transitions[current]

    def _narrow_to_resource(self, resource: ResourceT) -> Resource:
        """
        Narrow the type of the internal resource from its specific type (bound to ResourceABC)
        to the base Resource type for API compatibility.

        This method is used to ensure the public interface returns the more general type
        while the implementation can work with the more specific type internally.
        """
        return cast("Resource", resource)
