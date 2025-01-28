from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from scriptable.service.base.state import ServiceState

from .exceptions import RegistryError, RegistryKeyError, RegistryStateError
from .logger import logger

if TYPE_CHECKING:
    from scriptable.service.base import ServiceKey, ServiceType, Spec


class ServiceRegistry:
    """
    Thread-safe registry managing service instances and their lifecycle states.

    Primary responsibilities:
    - Maintain unique service instances based on factory and spec
    - Track and validate service lifecycle state transitions
    - Provide thread-safe access to service information

    This registry acts as the source of truth for service existence and state,
    but delegates relationship management to DependencyManager.
    """

    def __init__(self) -> None:
        self._instances: dict["ServiceKey", "ServiceType"] = {}
        self._states: dict["ServiceKey", ServiceState] = {}
        self._lock = Lock()
        logger.debug("Initialized service registry")

    def get_service(
        self,
        spec: "Spec",
    ) -> "ServiceType | None":
        """
        Retrieve existing service instance for given factory and spec.
        This is the primary deduplication mechanism - same factory+spec
        should always return the same instance.

        Args:
            spec: Service specification

        Returns:
            Existing service instance or None

        Raises:
            RegistryError: If key generation fails
        """
        key = spec.key
        service = self._instances.get(key, None)

        if service is not None:
            return self._instances.get(key)

        return None

    def add_service(
        self,
        service: "ServiceType",
    ) -> None:
        """
        Register new service instance. Should validate the service
        isn't already registered and initialize its state tracking.

        Args:
            service: Service instance to register

        Raises:
            RegistryError: If service already exists or is invalid
        """
        key = service.key

        with self._lock:
            if key in self._instances:
                raise RegistryError(f"Service already exists: '{service.readable_name}'")

            self._instances[key] = service
            self._states[key] = ServiceState.CREATED
            logger.debug(f"Registered service: '{service.readable_name}'")

    def remove_service(
        self,
        service: "ServiceType",
    ) -> None:
        """
        Remove service registration. Should verify the service is in a valid
        state for removal (not initialized/in use).

        Args:
            service: Service to remove

        Raises:
            RegistryError: If service not found or cannot be removed
        """
        key = service.key

        with self._lock:
            if key not in self._instances:
                raise RegistryKeyError(f"Service not found: '{service.readable_name}'")

            if self._states[key] not in (
                ServiceState.CREATED,
                ServiceState.SHUTDOWN,
                ServiceState.ERROR,
            ):
                raise RegistryStateError(f"Cannot remove service with state: '{self._states[key]}'")

            self._instances.pop(key)
            self._states.pop(key)
            logger.debug(f"Removed service: '{service.readable_name}'")

    def get_service_state(
        self,
        service: "ServiceType",
    ) -> ServiceState:
        """
        Get current lifecycle state of service.

        Args:
            service: Service to get state for

        Returns:
            Current service state

        Raises:
            RegistryKeyError: If service not found
        """
        key = service.key

        if key not in self._states:
            raise RegistryKeyError(f"Service not found: '{service.readable_name}'")

        return self._states[key]

    def set_service_state(
        self,
        service: "ServiceType",
        state: ServiceState,
    ) -> None:
        """
        Update service lifecycle state. Enforces valid state transitions
        and maintains thread safety.

        Args:
            service: Service to update
            state: New state

        Raises:
            RegistryError: If state transition is invalid
        """
        key = service.key

        with self._lock:
            if key not in self._states:
                raise RegistryKeyError(f"Service not found: '{service.readable_name}'")

            current = self._states[key]
            if not self._is_valid_transition(current, state):
                raise RegistryStateError(f"Invalid state transition: '{current}' -> '{state}'")

            self._states[key] = state
            logger.debug(f"Updated service state: '{service.readable_name}' -> '{state}'")

    def _is_valid_transition(
        self,
        current: ServiceState,
        new: ServiceState,
    ) -> bool:
        """Validate state transition."""

        # Implementation of state transition rules
        transitions = {
            ServiceState.CREATED: {ServiceState.INITIALIZING, ServiceState.ERROR},
            ServiceState.INITIALIZING: {ServiceState.INITIALIZED, ServiceState.ERROR},
            ServiceState.INITIALIZED: {ServiceState.SHUTTING_DOWN, ServiceState.ERROR},
            ServiceState.SHUTTING_DOWN: {ServiceState.SHUTDOWN, ServiceState.ERROR},
            ServiceState.SHUTDOWN: {ServiceState.INITIALIZING, ServiceState.ERROR},
            ServiceState.ERROR: set(),
        }
        return new in transitions[current]
