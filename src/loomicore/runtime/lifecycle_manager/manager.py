"""
Lifecycle Manager - Centralized resource lifecycle and state management.

This module provides the LifecycleManager which handles all resource lifecycle
operations including state transitions, hook execution, and dependency coordination.
It serves as the central authority for resource state management in the runtime system.

Note: This implementation is NOT thread-safe. Concurrent access protection will be
added in a future version. Currently suitable for single-threaded use or when
external synchronization is provided.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Generic, TypeVar

from loomicore.exceptions import InitializationError, ShutdownError
from loomicore.types import ResourceState

from .exceptions import LifecycleError, StateTransitionError
from .logger import logger

if TYPE_CHECKING:
    from loomicore.resource import Resource

    from ..composition_engine import CompositionEngine
    from ..dependency_manager import DependencyManager

__all__ = [
    "LifecycleManager",
]

ResourceT = TypeVar("ResourceT", bound="Resource")


class LifecycleManager(Generic[ResourceT]):
    """
    Centralized manager for resource lifecycle operations and state management.

    This manager handles:
    - Resource state tracking and validation
    - Lifecycle operations (initialize/shutdown)
    - Hook execution orchestration
    - Dependency lifecycle coordination
    - Mixed sync/async resource handling

    The manager serves as the single source of truth for resource lifecycle
    state and ensures consistent operations across the system.

    Design Features:
        - Owns resource state storage (moved from ResourceRegistry)
        - Validates state transitions before operations
        - Handles both sync and async resources seamlessly
        - Comprehensive error handling with proper state updates
        - Extensive logging for debugging and monitoring

    Note:
        This implementation is NOT thread-safe. Concurrent access protection
        will be added in a future version.
    """

    def __init__(
        self,
        dependency_manager: "DependencyManager[ResourceT]",
        composition_engine: "CompositionEngine[ResourceT]",
    ) -> None:
        """
        Initialize the lifecycle manager.

        Args:
            dependency_manager: Manager for resource relationships
            composition_engine: Engine for resolving attach descriptors
        """
        self._dependency_manager = dependency_manager
        self._composition_engine = composition_engine

        # State storage - this is now owned by LifecycleManager
        self._states: dict[str, ResourceState] = {}

        logger.debug("Initialized lifecycle manager")

    # === State Management ===

    def get_resource_state(self, resource: ResourceT) -> ResourceState:
        """
        Get current lifecycle state of resource.

        Args:
            resource: Resource to get state for

        Returns:
            Current resource state

        Notes:
            - Returns CREATED if resource not tracked yet
            - Used by BaseResource.resource_state property
        """
        return self._states.get(resource.key, ResourceState.CREATED)

    def set_resource_state(self, resource: ResourceT, state: ResourceState) -> None:
        """
        Update resource lifecycle state with validation.

        Args:
            resource: Resource to update
            state: New state to set

        Raises:
            StateTransitionError: If transition is invalid
            LifecycleError: If resource key is invalid

        Notes:
            - Validates state transitions before applying
            - Logs all state changes for debugging
        """
        key = resource.key
        if not key:
            raise LifecycleError(f"Invalid resource key for {resource.readable_name}")

        current_state = self._states.get(key, ResourceState.CREATED)

        if not self._is_valid_state_transition(current_state, state):
            raise StateTransitionError(
                f"Invalid state transition for '{resource.readable_name}': "
                f"'{current_state}' -> '{state}'"
            )

        self._states[key] = state
        logger.debug(
            f"State transition for '{resource.readable_name}': '{current_state}' -> '{state}'"
        )

    def is_resource_initialized(self, resource: ResourceT) -> bool:
        """
        Check if resource is fully initialized and ready for use.

        Args:
            resource: Resource to check

        Returns:
            True if resource is in INITIALIZED state

        Notes:
            - Used by BaseResource.is_initialized property
        """
        return self.get_resource_state(resource) == ResourceState.INITIALIZED

    def register_resource(self, resource: ResourceT) -> None:
        """
        Register a new resource for state tracking.

        Args:
            resource: Resource to register

        Notes:
            - Sets initial CREATED state
            - Idempotent - safe to call multiple times
        """
        key = resource.key
        if key not in self._states:
            self._states[key] = ResourceState.CREATED
            logger.debug(f"Registered resource for lifecycle tracking: '{resource.readable_name}'")

    def unregister_resource(self, resource: ResourceT) -> None:
        """
        Unregister resource from state tracking.

        Args:
            resource: Resource to unregister

        Notes:
            - Removes from state tracking
        """
        key = resource.key
        self._states.pop(key, None)
        logger.debug(f"Unregistered resource from lifecycle tracking: '{resource.readable_name}'")

    # === Lifecycle Operations ===

    def initialize_resource(self, resource: ResourceT) -> None:
        """
        Initialize synchronous resource and all its dependencies.

        This method handles the complete initialization process:
        1. Validates current state allows initialization
        2. Executes pre_initialize hook
        3. Composes attach descriptors (resolves dependencies)
        4. Initializes dependencies in proper order
        5. Calls user-defined setup() method
        6. Executes post_initialize hook
        7. Updates state to INITIALIZED

        Args:
            resource: Resource to initialize

        Raises:
            InitializationError: If initialization fails at any step
            StateTransitionError: If resource in invalid state for initialization

        Notes:
            - Idempotent - safe to call on already initialized resource
            - Sets ERROR state on any failure
            - Comprehensive logging for debugging
        """
        if self.is_resource_initialized(resource):
            logger.debug(f"Resource '{resource.readable_name}' already initialized, skipping")
            return

        current_state = self.get_resource_state(resource)
        if not self._is_valid_state_transition(current_state, ResourceState.INITIALIZING):
            raise StateTransitionError(
                f"Resource '{resource.readable_name}' cannot be initialized in state '{current_state}'"
            )

        try:
            logger.info(f"Initializing resource: '{resource.readable_name}'")

            # Execute pre-initialization hook
            self._execute_hook(resource, "pre_initialize", "pre-initialization")

            # Set initializing state
            self.set_resource_state(resource, ResourceState.INITIALIZING)

            # Compose dependencies (resolve attach descriptors)
            logger.debug(f"Composing dependencies for '{resource.readable_name}'")
            self._composition_engine.compose_resource(resource)

            # Initialize dependencies
            self._initialize_dependencies_sync(resource)

            # Execute user setup hook
            self._execute_hook(resource, "setup", "setup")

            # Set initialized state
            self.set_resource_state(resource, ResourceState.INITIALIZED)

            # Execute post-initialization hook
            self._execute_hook(resource, "post_initialize", "post-initialization")

            logger.info(f"Successfully initialized resource: '{resource.readable_name}'")

        except Exception as e:
            self.set_resource_state(resource, ResourceState.ERROR)
            logger.error(f"Failed to initialize resource '{resource.readable_name}': {str(e)}")
            raise InitializationError(
                f"Failed to initialize resource '{resource.readable_name}'"
            ) from e

    async def initialize_resource_async(self, resource: ResourceT) -> None:
        """
        Initialize asynchronous resource and all its dependencies.

        This method handles the complete async initialization process:
        1. Validates current state allows initialization
        2. Executes async pre_initialize hook
        3. Composes attach descriptors (resolves dependencies)
        4. Initializes dependencies in proper order (async-aware)
        5. Calls user-defined async setup() method
        6. Executes async post_initialize hook
        7. Updates state to INITIALIZED

        Args:
            resource: Resource to initialize

        Raises:
            InitializationError: If initialization fails at any step
            StateTransitionError: If resource in invalid state for initialization

        Notes:
            - Idempotent - safe to call on already initialized resource
            - Sets ERROR state on any failure
            - Handles mixed sync/async dependencies appropriately
        """
        if self.is_resource_initialized(resource):
            logger.debug(f"Resource '{resource.readable_name}' already initialized, skipping")
            return

        current_state = self.get_resource_state(resource)
        if not self._is_valid_state_transition(current_state, ResourceState.INITIALIZING):
            raise StateTransitionError(
                f"Resource '{resource.readable_name}' cannot be initialized in state '{current_state}'"
            )

        try:
            logger.info(f"Initializing async resource: '{resource.readable_name}'")

            # Execute pre-initialization hook
            await self._execute_hook_async(resource, "pre_initialize", "pre-initialization")

            # Set initializing state
            self.set_resource_state(resource, ResourceState.INITIALIZING)

            # Compose dependencies (resolve attach descriptors)
            logger.debug(f"Composing dependencies for '{resource.readable_name}'")
            self._composition_engine.compose_resource(resource)

            # Initialize dependencies
            await self._initialize_dependencies_async(resource)

            # Execute user setup hook
            await self._execute_hook_async(resource, "setup", "setup")

            # Set initialized state
            self.set_resource_state(resource, ResourceState.INITIALIZED)

            # Execute post-initialization hook
            await self._execute_hook_async(resource, "post_initialize", "post-initialization")

            logger.info(f"Successfully initialized async resource: '{resource.readable_name}'")

        except Exception as e:
            self.set_resource_state(resource, ResourceState.ERROR)
            logger.error(
                f"Failed to initialize async resource '{resource.readable_name}': {str(e)}"
            )
            raise InitializationError(
                f"Failed to initialize async resource '{resource.readable_name}'"
            ) from e

    def shutdown_resource(self, resource: ResourceT) -> None:
        """
        Shutdown synchronous resource and cleanup dependencies.

        This method handles the complete shutdown process:
        1. Validates current state allows shutdown
        2. Executes pre_shutdown hook
        3. Calls user-defined cleanup() method
        4. Shuts down orphaned dependencies
        5. Executes post_shutdown hook
        6. Updates state to SHUTDOWN

        Args:
            resource: Resource to shutdown

        Raises:
            ShutdownError: If shutdown fails at any step
            StateTransitionError: If resource in invalid state for shutdown

        Notes:
            - Handles orphaned dependency cleanup automatically
            - Sets ERROR state on failure
            - Logs all operations for debugging
        """
        current_state = self.get_resource_state(resource)
        if current_state == ResourceState.SHUTDOWN:
            logger.debug(f"Resource '{resource.readable_name}' already shut down, skipping")
            return

        if not self._is_valid_state_transition(current_state, ResourceState.SHUTTING_DOWN):
            raise StateTransitionError(
                f"Resource '{resource.readable_name}' cannot be shut down in state '{current_state}'"
            )

        try:
            logger.info(f"Shutting down resource: '{resource.readable_name}'")

            # Execute pre-shutdown hook
            self._execute_hook(resource, "pre_shutdown", "pre-shutdown")

            # Set shutting down state
            self.set_resource_state(resource, ResourceState.SHUTTING_DOWN)

            # Execute user cleanup hook
            self._execute_hook(resource, "cleanup", "cleanup")

            # Shutdown orphaned dependencies
            self._shutdown_dependencies_sync(resource)

            # Set shutdown state
            self.set_resource_state(resource, ResourceState.SHUTDOWN)

            # Execute post-shutdown hook
            self._execute_hook(resource, "post_shutdown", "post-shutdown")

            logger.info(f"Successfully shut down resource: '{resource.readable_name}'")

        except Exception as e:
            self.set_resource_state(resource, ResourceState.ERROR)
            logger.error(f"Failed to shutdown resource '{resource.readable_name}': {str(e)}")
            raise ShutdownError(f"Failed to shutdown resource '{resource.readable_name}'") from e

    async def shutdown_resource_async(self, resource: ResourceT) -> None:
        """
        Shutdown asynchronous resource and cleanup dependencies.

        This method handles the complete async shutdown process:
        1. Validates current state allows shutdown
        2. Executes async pre_shutdown hook
        3. Calls user-defined async cleanup() method
        4. Shuts down orphaned dependencies (async-aware)
        5. Executes async post_shutdown hook
        6. Updates state to SHUTDOWN

        Args:
            resource: Resource to shutdown

        Raises:
            ShutdownError: If shutdown fails at any step
            StateTransitionError: If resource in invalid state for shutdown

        Notes:
            - Handles orphaned dependency cleanup automatically
            - Sets ERROR state on failure
            - Handles mixed sync/async dependencies appropriately
        """
        current_state = self.get_resource_state(resource)
        if current_state == ResourceState.SHUTDOWN:
            logger.debug(f"Resource '{resource.readable_name}' already shut down, skipping")
            return

        if not self._is_valid_state_transition(current_state, ResourceState.SHUTTING_DOWN):
            raise StateTransitionError(
                f"Resource '{resource.readable_name}' cannot be shut down in state '{current_state}'"
            )

        try:
            logger.info(f"Shutting down async resource: '{resource.readable_name}'")

            # Execute pre-shutdown hook
            await self._execute_hook_async(resource, "pre_shutdown", "pre-shutdown")

            # Set shutting down state
            self.set_resource_state(resource, ResourceState.SHUTTING_DOWN)

            # Execute user cleanup hook
            await self._execute_hook_async(resource, "cleanup", "cleanup")

            # Shutdown orphaned dependencies
            await self._shutdown_dependencies_async(resource)

            # Set shutdown state
            self.set_resource_state(resource, ResourceState.SHUTDOWN)

            # Execute post-shutdown hook
            await self._execute_hook_async(resource, "post_shutdown", "post-shutdown")

            logger.info(f"Successfully shut down async resource: '{resource.readable_name}'")

        except Exception as e:
            self.set_resource_state(resource, ResourceState.ERROR)
            logger.error(f"Failed to shutdown async resource '{resource.readable_name}': {str(e)}")
            raise ShutdownError(
                f"Failed to shutdown async resource '{resource.readable_name}'"
            ) from e

    # === Private Implementation ===

    def _is_valid_state_transition(self, current: ResourceState, new: ResourceState) -> bool:
        """
        Validate resource state transition.

        Args:
            current: Current resource state
            new: Requested new state

        Returns:
            True if transition is valid

        Notes:
            - Defines the valid state machine for resource lifecycle
            - ERROR state can be reached from any state
            - SHUTDOWN resources can be re-initialized
        """
        transitions = {
            ResourceState.CREATED: {ResourceState.INITIALIZING, ResourceState.ERROR},
            ResourceState.INITIALIZING: {ResourceState.INITIALIZED, ResourceState.ERROR},
            ResourceState.INITIALIZED: {ResourceState.SHUTTING_DOWN, ResourceState.ERROR},
            ResourceState.SHUTTING_DOWN: {ResourceState.SHUTDOWN, ResourceState.ERROR},
            ResourceState.SHUTDOWN: {ResourceState.INITIALIZING, ResourceState.ERROR},
            ResourceState.ERROR: {ResourceState.INITIALIZING, ResourceState.SHUTTING_DOWN},
        }
        return new in transitions.get(current, set())

    def _execute_hook(self, resource: ResourceT, hook_name: str, description: str) -> None:
        """
        Execute synchronous lifecycle hook safely.

        Args:
            resource: Resource to execute hook on
            hook_name: Name of hook method to call
            description: Human-readable description for logging

        Notes:
            - Safely handles missing hooks (no-op)
            - Logs hook execution for debugging
            - Propagates exceptions to caller
        """
        if not hasattr(resource, hook_name):
            return

        hook_method = getattr(resource, hook_name)
        if not callable(hook_method):
            return

        logger.debug(f"Executing {description} hook for '{resource.readable_name}'")
        try:
            hook_method()
            logger.debug(f"Completed {description} hook for '{resource.readable_name}'")
        except Exception as e:
            logger.error(f"Failed {description} hook for '{resource.readable_name}': {str(e)}")
            raise

    async def _execute_hook_async(
        self, resource: ResourceT, hook_name: str, description: str
    ) -> None:
        """
        Execute asynchronous lifecycle hook safely.

        Args:
            resource: Resource to execute hook on
            hook_name: Name of hook method to call
            description: Human-readable description for logging

        Notes:
            - Safely handles missing hooks (no-op)
            - Handles both sync and async hook methods
            - Logs hook execution for debugging
            - Propagates exceptions to caller
        """
        if not hasattr(resource, hook_name):
            return

        hook_method = getattr(resource, hook_name)
        if not callable(hook_method):
            return

        logger.debug(f"Executing async {description} hook for '{resource.readable_name}'")
        try:
            if inspect.iscoroutinefunction(hook_method):
                await hook_method()
            else:
                hook_method()
            logger.debug(f"Completed async {description} hook for '{resource.readable_name}'")
        except Exception as e:
            logger.error(
                f"Failed async {description} hook for '{resource.readable_name}': {str(e)}"
            )
            raise

    def _initialize_dependencies_sync(self, resource: ResourceT) -> None:
        """
        Initialize all dependencies of a resource synchronously.

        Args:
            resource: Resource whose dependencies to initialize

        Raises:
            InitializationError: If any dependency initialization fails

        Notes:
            - Gets dependencies from dependency manager
            - Skips already initialized dependencies
            - Handles mixed sync/async dependencies
        """
        dependencies = self._dependency_manager.get_dependencies(resource)

        for name, dep in dependencies.items():
            if not hasattr(dep, "initialize") or not hasattr(dep, "is_initialized"):
                logger.debug(f"Dependency '{name}' of '{resource.readable_name}' has no lifecycle")
                continue

            if dep.is_initialized:
                logger.debug(
                    f"Dependency '{name}' of '{resource.readable_name}' already initialized"
                )
                continue

            try:
                logger.debug(f"Initializing dependency '{name}' of '{resource.readable_name}'")
                if inspect.iscoroutinefunction(dep.initialize):
                    raise InitializationError(
                        f"Dependency '{name}' of '{resource.readable_name}' is async, cannot initialize synchronously"
                    )

                dep.initialize()
                logger.debug(f"Initialized dependency '{name}' of '{resource.readable_name}'")
            except Exception as e:
                logger.error(
                    f"Failed to initialize dependency '{name}' of '{resource.readable_name}': {str(e)}"
                )
                raise InitializationError(f"Failed to initialize dependency '{name}'") from e

    async def _initialize_dependencies_async(self, resource: ResourceT) -> None:
        """
        Initialize all dependencies of a resource asynchronously.

        Args:
            resource: Resource whose dependencies to initialize

        Raises:
            InitializationError: If any dependency initialization fails

        Notes:
            - Gets dependencies from dependency manager
            - Skips already initialized dependencies
            - Handles mixed sync/async dependencies appropriately
        """
        dependencies = self._dependency_manager.get_dependencies(resource)

        for name, dep in dependencies.items():
            if not hasattr(dep, "initialize") or not hasattr(dep, "is_initialized"):
                logger.debug(f"Dependency '{name}' of '{resource.readable_name}' has no lifecycle")
                continue

            if dep.is_initialized:
                logger.debug(
                    f"Dependency '{name}' of '{resource.readable_name}' already initialized"
                )
                continue

            try:
                logger.debug(
                    f"Initializing async dependency '{name}' of '{resource.readable_name}'"
                )
                if inspect.iscoroutinefunction(dep.initialize):
                    await dep.initialize()
                else:
                    dep.initialize()
                logger.debug(f"Initialized async dependency '{name}' of '{resource.readable_name}'")
            except Exception as e:
                logger.error(
                    f"Failed to initialize async dependency '{name}' of '{resource.readable_name}': {str(e)}"
                )
                raise InitializationError(f"Failed to initialize dependency '{name}'") from e

    def _shutdown_dependencies_sync(self, resource: ResourceT) -> None:
        """
        Shutdown orphaned dependencies synchronously.

        Args:
            resource: Resource whose dependencies to check for shutdown

        Notes:
            - Detaches this resource as a dependent
            - Only shuts down dependencies that have no other dependents
            - Handles mixed sync/async dependencies
        """
        dependencies = self._dependency_manager.get_dependencies(resource)

        for name, dep in dependencies.items():
            # Detach this resource as a dependent
            self._dependency_manager.detach_relationship(resource, dep)

            if not hasattr(dep, "shutdown"):
                logger.debug(f"Dependency '{name}' has no shutdown method")
                continue

            # Check if dependency can be auto-shutdown (no other dependents)
            if not self._dependency_manager.can_auto_shutdown(dep):
                logger.debug(f"Dependency '{name}' still has other dependents, not shutting down")
                continue

            try:
                logger.debug(f"Auto-shutting down orphaned dependency '{name}'")
                if inspect.iscoroutinefunction(dep.initialize):
                    raise ShutdownError(
                        f"Dependency '{name}' of '{resource.readable_name}' is async, cannot shutdown synchronously"
                    )

                dep.shutdown()
                logger.debug(f"Auto-shut down orphaned dependency '{name}'")
            except Exception as e:
                logger.error(f"Failed to shutdown orphaned dependency '{name}': {str(e)}")
                # Continue with other dependencies, don't fail the main shutdown

    async def _shutdown_dependencies_async(self, resource: ResourceT) -> None:
        """
        Shutdown orphaned dependencies asynchronously.

        Args:
            resource: Resource whose dependencies to check for shutdown

        Notes:
            - Detaches this resource as a dependent
            - Only shuts down dependencies that have no other dependents
            - Handles mixed sync/async dependencies appropriately
        """
        dependencies = self._dependency_manager.get_dependencies(resource)

        for name, dep in dependencies.items():
            # Detach this resource as a dependent
            self._dependency_manager.detach_relationship(resource, dep)

            if not hasattr(dep, "shutdown"):
                logger.debug(f"Dependency '{name}' has no shutdown method")
                continue

            # Check if dependency can be auto-shutdown (no other dependents)
            if not self._dependency_manager.can_auto_shutdown(dep):
                logger.debug(f"Dependency '{name}' still has other dependents, not shutting down")
                continue

            try:
                logger.debug(f"Auto-shutting down orphaned async dependency '{name}'")
                if inspect.iscoroutinefunction(dep.shutdown):
                    await dep.shutdown()
                else:
                    dep.shutdown()
                logger.debug(f"Auto-shut down orphaned async dependency '{name}'")
            except Exception as e:
                logger.error(f"Failed to shutdown orphaned async dependency '{name}': {str(e)}")
                # Continue with other dependencies, don't fail the main shutdown
