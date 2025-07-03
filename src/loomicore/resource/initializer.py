from __future__ import annotations

from asyncio import Lock as AsyncLock
from inspect import iscoroutinefunction
from threading import Lock as ThreadLock
from types import TracebackType
from typing import TYPE_CHECKING, Self, cast

from ..exceptions import InitializationError, ShutdownError
from ..registry import RegistryError
from ..types import ResourceState
from .base import AsyncResourceABC, ResourceABC, SyncResourceABC
from .logger import logger

if TYPE_CHECKING:
    pass


class BaseResourceInitializer(ResourceABC):
    """
    Async implementation of resource initialization and lifecycle management.

    This mixin provides async implementations for resource initialization,
    shutdown, and lifecycle management. It should be used with BaseResource
    for async resource implementations.
    """

    @property
    def resource_state(self) -> ResourceState:
        """
        Current resource lifecycle state.

        Returns:
            Current ResourceState or ERROR if state unavailable
        """
        try:
            return self._registry.get_resource_state(self)
        except RegistryError:
            return ResourceState.ERROR

    @property
    def is_initialized(self) -> bool:
        """Check if resource is fully initialized."""
        return self.resource_state == ResourceState.INITIALIZED

    def __repr__(self) -> str:
        """String representation including spec."""
        return f"<Resource '{self.readable_name}' ('{self.resource_state}'): spec=({self.spec})>"


class AsyncResourceInitializer(BaseResourceInitializer, AsyncResourceABC):
    _resource_lock: AsyncLock

    async def initialize(self) -> None:
        """
        Initialize resource and its dependencies asynchronously.

        This method handles the complete initialization process:
        1. Validates resource state
        2. Initializes dependencies
        3. Performs resource-specific initialization
        4. Updates resource state

        Raises:
            InitializationError: If initialization fails
            ResourceStateError: If resource in invalid state
        """
        if not hasattr(self, "_resource_lock"):
            self._resource_lock = AsyncLock()

        if not self._registry.is_valid_state_transition(
            self.resource_state, ResourceState.INITIALIZING
        ):
            logger.error(
                f"Resource '{self.readable_name}' can not be initialized in state '{self.resource_state}'"
            )
            raise InitializationError(
                f"Resource '{self.readable_name}' can not be initialized in state '{self.resource_state}'"
            )

        async with self._resource_lock:
            # Execute pre-initialization hook
            try:
                logger.debug(f"Running pre-initialization for '{self.readable_name}'")
                await self.pre_initialize()
                logger.debug(f"Pre-initialization complete for '{self.readable_name}'")
            except Exception as e:
                logger.error(f"Failed to pre-initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(f"Failed to pre-initialize '{self.readable_name}'") from e

            try:
                self._registry.set_resource_state(self, ResourceState.INITIALIZING)

                # Do actual initialization
                await self._init_impl()

                # Do resource-specific setup
                await self.setup()

                self._registry.set_resource_state(self, ResourceState.INITIALIZED)
                logger.info(f"Initialized resource: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_resource_state(self, ResourceState.ERROR)
                logger.error(f"Failed to initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(f"Failed to initialize '{self.readable_name}'") from e

            # Execute post-initialization hook
            try:
                logger.debug(f"Running post-initialization for '{self.readable_name}'")
                await self.post_initialize()
                logger.debug(f"Post-initialization complete for '{self.readable_name}'")
            except Exception as e:
                logger.error(f"Failed to post-initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(
                    f"Failed to post-initialize '{self.readable_name}'"
                ) from e

    async def shutdown(self) -> None:
        """
        Shutdown resource and cleanup dependencies asynchronously.

        This method handles the complete shutdown process:
        1. Validates resource state
        2. Performs resource-specific shutdown
        3. Cleans up orphaned dependencies
        4. Updates resource state

        Raises:
            ShutdownError: If shutdown fails
            ResourceStateError: If resource in invalid state
        """
        if not self._registry.is_valid_state_transition(
            self.resource_state, ResourceState.SHUTTING_DOWN
        ):
            logger.error(
                f"Resource '{self.readable_name}' can not be shut down in state '{self.resource_state}'"
            )
            raise ShutdownError(
                f"Resource '{self.readable_name}' can not be shut down in state '{self.resource_state}'"
            )

        async with self._resource_lock:
            # Execute pre-shutdown hook
            try:
                await self.pre_shutdown()
            except Exception as e:
                logger.error(f"Failed to pre-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to pre-shutdown '{self.readable_name}'") from e

            try:
                self._registry.set_resource_state(self, ResourceState.SHUTTING_DOWN)

                # Perform resource-specific cleanup first
                await self.cleanup()

                # Do actual shutdown
                await self._shutdown_impl()

                self._registry.set_resource_state(self, ResourceState.SHUTDOWN)

                logger.info(f"Shut down resource: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_resource_state(self, ResourceState.ERROR)
                logger.error(f"Failed to shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown '{self.readable_name}'") from e

            # Execute post-shutdown hook
            try:
                await self.post_shutdown()
            except Exception as e:
                logger.error(f"Failed to post-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to post-shutdown '{self.readable_name}'") from e

    async def _init_impl(self) -> None:
        # Initializations realted to composer mixin
        self._initialize_attach_descriptors()

        # Initialize dependencies
        await self._init_dependencies()

    async def _shutdown_impl(self) -> None:
        # Shutdown dependencies
        await self._shutdown_dependencies()

    # --- Helpers --- #

    async def _init_dependencies(self) -> None:
        """
        Initialize all resource dependencies asynchronously.

        Ensures all dependencies are initialized before the resource.

        Raises:
            InitializationError: If dependency initialization fails
        """
        # Get all dependencies
        deps = self._get_dependencies()

        # Initialize each dependency
        for name, dep in deps.items():
            if not hasattr(dep, "initialize"):
                continue

            if dep.is_initialized:
                continue

            dep = cast(SyncResourceABC, dep)

            try:
                if iscoroutinefunction(dep.initialize):
                    dep = cast(AsyncResourceABC, dep)
                    await dep.initialize()
                else:
                    dep.initialize()
            except Exception as e:
                logger.error(
                    f"Failed to initialize dependency '{name}' of '{self.readable_name}': {str(e)}"
                )
                raise InitializationError(f"Failed to initialize dependency '{name}'") from e

    async def _shutdown_dependencies(self) -> None:
        """
        Shutdown resource dependencies asynchronously.

        Raises:
            ShutdownError: If dependency shutdown fails
        """
        # Find and cleanup orphaned dependencies
        deps = self._get_dependencies()

        # Shutdown orphans
        for dep in deps.values():
            dep._detach_dependent(self)

            if not hasattr(dep, "shutdown"):
                continue

            if not self._dep_manager.can_auto_shutdown(dep):
                continue

            dep = cast(SyncResourceABC, dep)

            try:
                if iscoroutinefunction(dep.shutdown):
                    dep = cast(AsyncResourceABC, dep)
                    await dep.shutdown()
                else:
                    dep.shutdown()

            except Exception as e:
                logger.error(f"Failed to shutdown dependency '{dep.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown dependency '{dep.readable_name}'") from e

    # --- Context Manager Support --- #

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing resource.

        Returns:
            Self for context usage
        """
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down resource."""
        await self.shutdown()

    # --- Lifecycle Methods --- #

    async def setup(self) -> None:
        """
        Resource-specific setup.

        This method should be implemented by concrete resources to
        perform their specific setup requirements
        (opening connections, configuring resource, etc).
        """
        pass

    async def cleanup(self) -> None:
        """
        Resource-specific cleanup.

        This method should be implemented by concrete resources to
        perform their specific cleanup requirements.
        """
        pass

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before resource initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        pass

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after resource initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        pass

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before resource shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        pass

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after resource shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        pass


class SyncResourceInitializer(BaseResourceInitializer, SyncResourceABC):
    _resource_lock: ThreadLock

    def initialize(self) -> None:
        """
        Initialize resource and its dependencies asynchronously.

        This method handles the complete initialization process:
        1. Validates resource state
        2. Initializes dependencies
        3. Performs resource-specific initialization
        4. Updates resource state

        Raises:
            InitializationError: If initialization fails
            ResourceStateError: If resource in invalid state
        """
        if not hasattr(self, "_resource_lock"):
            self._resource_lock = ThreadLock()

        if not self._registry.is_valid_state_transition(
            self.resource_state, ResourceState.INITIALIZING
        ):
            logger.error(
                f"Resource '{self.readable_name}' can not be initialized in state '{self.resource_state}'"
            )
            raise InitializationError(
                f"Resource '{self.readable_name}' can not be initialized in state '{self.resource_state}'"
            )

        with self._resource_lock:
            # Execute pre-initialization hook
            try:
                logger.debug(f"Running pre-initialization for '{self.readable_name}'")
                self.pre_initialize()
                logger.debug(f"Pre-initialization complete for '{self.readable_name}'")
            except Exception as e:
                logger.error(f"Failed to pre-initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(f"Failed to pre-initialize '{self.readable_name}'") from e

            try:
                self._registry.set_resource_state(self, ResourceState.INITIALIZING)

                # Do actual initialization
                self._init_impl()

                # Do resource-specific setup
                self.setup()

                self._registry.set_resource_state(self, ResourceState.INITIALIZED)
                logger.info(f"Initialized resource: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_resource_state(self, ResourceState.ERROR)
                logger.error(f"Failed to initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(f"Failed to initialize '{self.readable_name}'") from e

            # Execute post-initialization hook
            try:
                logger.debug(f"Running post-initialization for '{self.readable_name}'")
                self.post_initialize()
                logger.debug(f"Post-initialization complete for '{self.readable_name}'")
            except Exception as e:
                logger.error(f"Failed to post-initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(
                    f"Failed to post-initialize '{self.readable_name}'"
                ) from e

    def shutdown(self) -> None:
        """
        Shutdown resource and cleanup dependencies asynchronously.

        This method handles the complete shutdown process:
        1. Validates resource state
        2. Performs resource-specific shutdown
        3. Cleans up orphaned dependencies
        4. Updates resource state

        Raises:
            ShutdownError: If shutdown fails
            ResourceStateError: If resource in invalid state
        """
        if not self._registry.is_valid_state_transition(
            self.resource_state, ResourceState.SHUTTING_DOWN
        ):
            logger.error(
                f"Resource '{self.readable_name}' can not be shut down in state '{self.resource_state}'"
            )
            raise ShutdownError(
                f"Resource '{self.readable_name}' can not be shut down in state '{self.resource_state}'"
            )

        with self._resource_lock:
            # Execute pre-shutdown hook
            try:
                self.pre_shutdown()
            except Exception as e:
                logger.error(f"Failed to pre-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to pre-shutdown '{self.readable_name}'") from e

            try:
                self._registry.set_resource_state(self, ResourceState.SHUTTING_DOWN)

                # Perform resource-specific cleanup first
                self.cleanup()

                # Do acutal shutdown
                self._shutdown_impl()

                self._registry.set_resource_state(self, ResourceState.SHUTDOWN)

                logger.info(f"Shut down resource: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_resource_state(self, ResourceState.ERROR)
                logger.error(f"Failed to shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown '{self.readable_name}'") from e

            # Execute post-shutdown hook
            try:
                self.post_shutdown()
            except Exception as e:
                logger.error(f"Failed to post-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to post-shutdown '{self.readable_name}'") from e

    def _init_impl(self) -> None:
        # Do composer-related inits
        self._initialize_attach_descriptors()

        # Initialize dependencies first
        self._init_dependencies()

    def _shutdown_impl(self) -> None:
        # Shutdown dependencies first
        self._shutdown_dependencies()

    # --- Helpers --- #

    def _init_dependencies(self) -> None:
        """
        Initialize all resource dependencies asynchronously.

        Ensures all dependencies are initialized before the resource.

        Raises:
            InitializationError: If dependency initialization fails
        """
        # Get all dependencies
        deps = self._get_dependencies()

        # Initialize each dependency
        for name, dep in deps.items():
            if not hasattr(dep, "initialize"):
                continue

            if dep.is_initialized:
                continue

            dep = cast(SyncResourceABC, dep)

            try:
                if iscoroutinefunction(dep.initialize):
                    raise ShutdownError("Async shutdown not supported")
                else:
                    dep.initialize()
            except Exception as e:
                logger.error(
                    f"Failed to initialize dependency '{name}' of '{self.readable_name}': {str(e)}"
                )
                raise InitializationError(f"Failed to initialize dependency '{name}'") from e

    def _shutdown_dependencies(self) -> None:
        """
        Shutdown resource dependencies asynchronously.

        Raises:
            ShutdownError: If dependency shutdown fails
        """
        # Find and cleanup orphaned dependencies
        deps = self._get_dependencies()

        # Shutdown orphans
        for dep in deps.values():
            dep._detach_dependent(self)

            if not hasattr(dep, "shutdown"):
                continue

            if not self._dep_manager.can_auto_shutdown(dep):
                continue

            dep = cast(SyncResourceABC, dep)

            try:
                if iscoroutinefunction(dep.shutdown):
                    raise InitializationError("Async shutdown not supported")
                else:
                    dep.shutdown()

            except Exception as e:
                logger.error(f"Failed to shutdown dependency '{dep.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown dependency '{dep.readable_name}'") from e

    # --- Context Manager Support --- #

    def __enter__(self) -> Self:
        """
        Enter async context, initializing resource.

        Returns:
            Self for context usage
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down resource."""
        self.shutdown()

    # --- Lifecycle Methods --- #

    def setup(self) -> None:
        """
        Resource-specific setup.

        This method should be implemented by concrete resources to
        perform their specific setup requirements
        (opening connections, configuring resource, etc).
        """
        pass

    def cleanup(self) -> None:
        """
        Resource-specific cleanup.

        This method should be implemented by concrete resources to
        perform their specific cleanup requirements.
        """
        pass

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before resource initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        pass

    def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after resource initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        pass

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before resource shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        pass

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after resource shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        pass
