from __future__ import annotations

from asyncio import Lock
from inspect import iscoroutinefunction
from types import TracebackType
from typing import Self, cast

from scriptable.service.base import ServiceAsyncBase, ServiceState
from scriptable.service.protocols import ServiceAsyncProtocol, ServiceSyncProtocol

from .base import ServiceCommonInitializer
from .exceptions import InitializationError, ShutdownError
from .logger import logger


class ServiceInitializer(ServiceCommonInitializer, ServiceAsyncBase):
    async def initialize(self) -> None:
        """
        Initialize service and its dependencies asynchronously.

        This method handles the complete initialization process:
        1. Validates service state
        2. Initializes dependencies
        3. Performs service-specific initialization
        4. Updates service state

        Raises:
            InitializationError: If initialization fails
            ServiceStateError: If service in invalid state
        """
        if not hasattr(self, "_lock"):
            self._lock = Lock()

        if not self._registry._is_valid_transition(self.service_state, ServiceState.INITIALIZING):
            logger.error(
                f"Service '{self.readable_name}' can not be initialized in state '{self.service_state}'"
            )
            raise InitializationError(
                f"Service '{self.readable_name}' can not be initialized in state '{self.service_state}'"
            )

        async with self._lock:
            # Execute pre-initialization hook
            try:
                logger.debug(f"Running pre-initialization for '{self.readable_name}'")
                await self.pre_initialize()
                logger.debug(f"Pre-initialization complete for '{self.readable_name}'")
            except Exception as e:
                logger.error(f"Failed to pre-initialize '{self.readable_name}': {str(e)}")
                raise InitializationError(f"Failed to pre-initialize '{self.readable_name}'") from e

            try:
                self._registry.set_service_state(self, ServiceState.INITIALIZING)

                # Initialize dependencies first
                await self._init_dependencies()

                # Do service-specific setup
                await self.setup()

                self._registry.set_service_state(self, ServiceState.INITIALIZED)
                logger.info(f"Initialized service: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_service_state(self, ServiceState.ERROR)
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
        Shutdown service and cleanup dependencies asynchronously.

        This method handles the complete shutdown process:
        1. Validates service state
        2. Performs service-specific shutdown
        3. Cleans up orphaned dependencies
        4. Updates service state

        Raises:
            ShutdownError: If shutdown fails
            ServiceStateError: If service in invalid state
        """
        if not self._registry._is_valid_transition(self.service_state, ServiceState.SHUTTING_DOWN):
            logger.error(
                f"Service '{self.readable_name}' can not be shut down in state '{self.service_state}'"
            )
            raise ShutdownError(
                f"Service '{self.readable_name}' can not be shut down in state '{self.service_state}'"
            )

        async with self._lock:
            # Execute pre-shutdown hook
            try:
                await self.pre_shutdown()
            except Exception as e:
                logger.error(f"Failed to pre-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to pre-shutdown '{self.readable_name}'") from e

            try:
                self._registry.set_service_state(self, ServiceState.SHUTTING_DOWN)

                # Perform service-specific cleanup first
                await self.cleanup()

                # Shutdown dependencies
                await self._shutdown_dependencies()

                self._registry.set_service_state(self, ServiceState.SHUTDOWN)

                logger.info(f"Shut down service: '{self.readable_name}'")
            except Exception as e:
                self._registry.set_service_state(self, ServiceState.ERROR)
                logger.error(f"Failed to shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown '{self.readable_name}'") from e

            # Execute post-shutdown hook
            try:
                await self.post_shutdown()
            except Exception as e:
                logger.error(f"Failed to post-shutdown '{self.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to post-shutdown '{self.readable_name}'") from e

    async def _init_dependencies(self) -> None:
        """
        Initialize all service dependencies asynchronously.

        Ensures all dependencies are initialized before the service.

        Raises:
            InitializationError: If dependency initialization fails
        """
        # Get all dependencies
        deps = self.get_dependencies()

        # Initialize each dependency
        for name, dep in deps.items():
            if not hasattr(dep, "initialize"):
                continue

            if dep.is_initialized:
                continue

            dep = cast(ServiceSyncProtocol, dep)

            try:
                if iscoroutinefunction(dep.initialize):
                    dep = cast(ServiceAsyncProtocol, dep)
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
        Shutdown service dependencies asynchronously.

        Raises:
            ShutdownError: If dependency shutdown fails
        """
        # Find and cleanup orphaned dependencies
        deps = self.get_dependencies()

        # Shutdown orphans
        for dep in deps.values():
            dep.detach_dependent(self)

            if not hasattr(dep, "shutdown"):
                continue

            if not self._dep_manager.can_auto_shutdown(dep):
                continue

            dep = cast(ServiceSyncProtocol, dep)

            try:
                if iscoroutinefunction(dep.shutdown):
                    dep = cast(ServiceAsyncProtocol, dep)
                    await dep.shutdown()
                else:
                    dep.shutdown()

            except Exception as e:
                logger.error(f"Failed to shutdown dependency '{dep.readable_name}': {str(e)}")
                raise ShutdownError(f"Failed to shutdown dependency '{dep.readable_name}'") from e

    # --- Context Manager Support --- #

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing service.

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
        """Exit async context, shutting down service."""
        await self.shutdown()

    # --- Abstract Methods --- #

    async def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        pass

    async def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        pass

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        pass

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        pass

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        pass

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        pass
