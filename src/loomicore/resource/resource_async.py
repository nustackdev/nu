"""
AsyncResource - asynchronous resource implementation.

This module provides the AsyncResource class for building asynchronous services
with automatic dependency injection and lifecycle management. AsyncResource
provides a clean, declarative interface while delegating all operational
complexity to the runtime system.

Features:
- Declarative dependency injection via Attach descriptors
- Asynchronous lifecycle management (initialize/shutdown)
- Async context manager support for resource cleanup
- User-overridable async setup/cleanup hooks
- Concurrent-safe operations through runtime delegation

The class maintains the separation between user interface and implementation
by providing intuitive async methods that delegate to the runtime system for
all complex operations.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self, final

from loomicore.runtime import get_lifecycle_manager

from .base import BaseResource
from .meta import ResourceMeta

__all__ = [
    "AsyncResource",
]


class AsyncResource(BaseResource, metaclass=ResourceMeta):
    """
    Asynchronous resource with lifecycle management and dependency injection.

    AsyncResource provides the foundation for building asynchronous services
    with automatic dependency management. It combines a clean, declarative
    interface with powerful runtime capabilities through delegation.

    Key Features:
        - Automatic dependency injection via Attach descriptors
        - Asynchronous lifecycle management with user-overridable hooks
        - Async context manager support for automatic cleanup
        - Concurrent-safe operations through runtime coordination
        - Resource deduplication based on specifications

    Usage Pattern:
        ```python
        class AsyncDatabaseService(AsyncResource):
            cache = Attach(AsyncCacheSpec())
            connection_pool = Attach(AsyncConnectionPoolSpec())

            async def setup(self):
                # Dependencies automatically resolved and available
                await self.connection_pool.connect()
                await self.cache.initialize()

            async def cleanup(self):
                await self.connection_pool.disconnect()
                await self.cache.shutdown()

            async def query(self, sql: str):
                # Use dependencies in business logic
                result = await self.connection_pool.execute(sql)
                await self.cache.store(sql, result)
                return result

        # Simple usage with automatic lifecycle
        async with AsyncDatabaseService(spec) as db:
            result = await db.query("SELECT * FROM users")
        ```

    Lifecycle:
        1. Creation: Resource created via metaclass delegation to runtime
        2. Composition: Runtime resolves Attach descriptors automatically
        3. Initialization: Dependencies initialized, then setup() called
        4. Usage: Resource available for business operations
        5. Shutdown: cleanup() called, then dependencies shut down

    Design Notes:
        - All operational logic delegated to runtime system
        - Function-level imports prevent circular dependencies
        - User hooks (setup/cleanup) for resource-specific async logic
        - Async context manager ensures proper cleanup even on exceptions
        - Concurrent-safe through runtime coordination
    """

    # === Async Lifecycle Methods ===

    @final
    async def initialize(self) -> None:
        """
        Asynchronously initialize the resource and all its dependencies.

        This method handles the complete async initialization process:
        1. Validates resource state and prerequisites
        2. Resolves and initializes all Attach descriptors
        3. Initializes dependencies in proper order (async-aware)
        4. Calls user-defined async setup() method
        5. Updates resource state to INITIALIZED

        The method is idempotent - calling it on an already initialized
        resource is safe and will not cause duplicate initialization.

        Raises:
            InitializationError: If initialization fails at any step
            DependencyError: If dependency resolution or initialization fails
            StateError: If resource is in invalid state for initialization

        Notes:
            - All complexity handled by runtime system
            - User logic should go in async setup() method, not here
            - Concurrent-safe through runtime coordination
            - Automatic dependency ordering prevents circular dependencies
            - Handles mixed sync/async dependencies appropriately
        """
        await get_lifecycle_manager().initialize_resource_async(self)

    @final
    async def shutdown(self) -> None:
        """
        Asynchronously shutdown the resource and clean up all dependencies.

        Note: This method unregisters the ROOT role for this resource
        before proceeding with shutdown. Validates resource state
        and prerequisites before proceeding with shutdown.

        This method handles the complete async shutdown process:
        1. Validates resource state and shutdown prerequisites
        2. Calls user-defined async cleanup() method
        3. Shuts down dependencies in reverse initialization order
        4. Performs final cleanup and state updates
        5. Updates resource state to SHUTDOWN

        The method handles orphaned dependency cleanup automatically,
        shutting down dependencies that are no longer needed by other resources.

        Raises:
            ShutdownError: If shutdown fails at any step
            StateError: If resource is in invalid state for shutdown

        Notes:
            - All complexity handled by runtime system
            - User logic should go in async cleanup() method, not here
            - Concurrent-safe through runtime coordination
            - Smart dependency cleanup prevents resource leaks
            - Handles mixed sync/async dependencies appropriately
        """
        await get_lifecycle_manager().shutdown_resource_async(self)

    @final
    async def shutdown_as_dependency(self) -> None:
        """
        Asynchronously shutdown the resource and clean up all dependencies.

        Note: This method does not unregister the ROOT role for this resource.
        It is intended to be called when the resource is being shut down
        as part of a dependency chain, not as a root resource.

        This method handles the complete async shutdown process:
        1. Validates resource state and shutdown prerequisites
        2. Calls user-defined async cleanup() method
        3. Shuts down dependencies in reverse initialization order
        4. Performs final cleanup and state updates
        5. Updates resource state to SHUTDOWN

        The method handles orphaned dependency cleanup automatically,
        shutting down dependencies that are no longer needed by other resources.

        Raises:
            ShutdownError: If shutdown fails at any step
            StateError: If resource is in invalid state for shutdown

        Notes:
            - All complexity handled by runtime system
            - User logic should go in async cleanup() method, not here
            - Concurrent-safe through runtime coordination
            - Smart dependency cleanup prevents resource leaks
            - Handles mixed sync/async dependencies appropriately
        """
        await get_lifecycle_manager().shutdown_resource_as_dependency_async(self)

    # === User-Overridable Async Hooks ===

    async def setup(self) -> None:
        """
        Async resource-specific setup logic called during initialization.

        This method is called by the runtime after all dependencies have
        been resolved and initialized. Override this method to implement
        resource-specific async initialization logic such as:
        - Opening async connections or files
        - Configuring internal async state
        - Setting up async caches or pools
        - Registering async callbacks or handlers

        When this method is called:
        - All Attach descriptors have been resolved to actual resources
        - All dependencies are fully initialized and ready for use
        - Resource is in INITIALIZING state

        Example:
            ```python
            async def setup(self):
                # Dependencies are available and initialized
                await self.database.connect()
                await self.cache.warm_up()
                await self.metrics.start_collection()
            ```

        Notes:
            - Called automatically by runtime during initialization
            - Dependencies guaranteed to be available and initialized
            - Exceptions will abort initialization and set ERROR state
            - Keep this method focused on setup, not business logic
            - Can await async operations safely
        """
        pass

    async def cleanup(self) -> None:
        """
        Async resource-specific cleanup logic called during shutdown.

        This method is called by the runtime before dependencies are
        shut down. Override this method to implement resource-specific
        async cleanup logic such as:
        - Closing async connections or files
        - Flushing async caches or buffers
        - Saving state or data asynchronously
        - Unregistering async callbacks or handlers

        When this method is called:
        - Resource is in SHUTTING_DOWN state
        - Dependencies are still available and operational
        - Shutdown process has been initiated

        Example:
            ```python
            async def cleanup(self):
                # Dependencies still available for final operations
                await self.cache.flush()
                await self.database.save_pending_data()
                await self.metrics.stop_collection()
            ```

        Notes:
            - Called automatically by runtime during shutdown
            - Dependencies still available for final operations
            - Exceptions logged but don't prevent shutdown completion
            - Keep this method focused on cleanup, not business logic
            - Can await async operations safely
        """
        pass

    async def pre_initialize(self) -> None:
        """
        Async pre-initialization hook called before resource initialization begins.

        This method is called by the runtime before any initialization logic
        starts. Override this method to implement async validation, preparation,
        or setup logic that must happen before dependencies are resolved.

        When this method is called:
        - Resource is in CREATED state
        - No dependencies have been resolved yet
        - No initialization has occurred
        - Resource state validation has not yet happened

        Common use cases:
        - Validate configuration or environment asynchronously
        - Prepare external resources or connections
        - Set up async logging or monitoring
        - Perform async security checks

        Example:
            ```python
            async def pre_initialize(self):
                # Validate configuration before proceeding
                if not self.spec.database_url:
                    raise ValueError("Database URL required")
                # Prepare external state asynchronously
                await self._ensure_database_exists()
                await self._check_credentials()
            ```

        Raises:
            InitializationError: If pre-initialization checks fail

        Notes:
            - Called before dependency resolution
            - Exceptions will abort initialization
            - Use for async validation and preparation logic
            - Keep focused on prerequisites, not main setup
            - Can safely await async operations
        """
        pass

    async def pre_shutdown(self) -> None:
        """
        Async pre-shutdown hook called before resource shutdown begins.

        This method is called by the runtime before any shutdown logic
        starts. Override this method to implement async preparation logic
        that must happen before the main cleanup begins.

        When this method is called:
        - Resource is in INITIALIZED state
        - All dependencies are still available and operational
        - No shutdown logic has started yet
        - Resource is still fully functional

        Common use cases:
        - Save critical state or data asynchronously
        - Notify clients of impending shutdown via async calls
        - Gracefully finish async in-progress operations
        - Prepare for clean async shutdown

        Example:
            ```python
            async def pre_shutdown(self):
                # Notify clients of shutdown asynchronously
                await self.broadcast_shutdown_notice()
                # Finish pending async operations
                await self.complete_pending_requests()
                # Save critical state
                await self.save_checkpoint()
            ```

        Raises:
            ShutdownError: If pre-shutdown logic fails

        Notes:
            - Called before main cleanup begins
            - Dependencies still fully available
            - Use for graceful async shutdown preparation
            - Exceptions will be logged but won't prevent shutdown
            - Can safely await async operations
        """
        pass

    async def post_shutdown(self) -> None:
        """
        Async post-shutdown hook called after resource shutdown completes.

        This method is called by the runtime after all shutdown logic
        has completed. Override this method to implement async finalization
        logic that should happen after the resource is fully shut down.

        When this method is called:
        - Resource is in SHUTDOWN state
        - All dependencies have been shut down
        - User cleanup() method has completed
        - Resource is no longer operational

        Common use cases:
        - Unregister from external services asynchronously
        - Clean up async temporary files or resources
        - Emit async shutdown events or notifications
        - Perform final async cleanup tasks

        Example:
            ```python
            async def post_shutdown(self):
                # Unregister from service discovery
                await self.service_registry.unregister(self.name)
                # Clean up temp files asynchronously
                await self.cleanup_temp_files()
                # Send final notifications
                await self.notify_shutdown_complete()
            ```

        Raises:
            ShutdownError: If post-shutdown logic fails

        Notes:
            - Called after all shutdown is complete
            - Dependencies no longer available
            - Exceptions logged but don't affect shutdown status
            - Use for final async cleanup and unregistration
            - Can safely await async operations
        """
        pass

    async def post_initialize(self) -> None:
        """
        Async post-initialization hook called after resource initialization completes.

        This method is called by the runtime after all initialization logic
        has completed successfully. Override this method to implement async
        finalization, registration, or startup logic that should happen
        after the resource is fully operational.

        When this method is called:
        - Resource is in INITIALIZED state
        - All dependencies are resolved and initialized
        - User setup() method has completed
        - Resource is fully operational

        Common use cases:
        - Register with external services asynchronously
        - Start background async tasks or workers
        - Emit async startup events or notifications
        - Perform async health checks or warming

        Example:
            ```python
            async def post_initialize(self):
                # Register with service discovery
                await self.service_registry.register(self.name, self.endpoint)
                # Start background maintenance tasks
                await self.start_background_workers()
                # Warm up caches
                await self.warm_caches()
            ```

        Raises:
            InitializationError: If post-initialization logic fails

        Notes:
            - Called after all initialization is complete
            - Resource is fully operational when this runs
            - Exceptions will mark resource as ERROR state
            - Use for async finalization and registration logic
            - Can safely await async operations
        """
        pass

    # === Async Context Manager Support ===

    async def __aenter__(self) -> Self:
        """
        Enter asynchronous context manager, initializing the resource.

        Automatically initializes the resource when entering an 'async with' block,
        ensuring it's ready for use within the context.

        Returns:
            Self for use within the async context block

        Example:
            ```python
            async with AsyncDatabaseService(spec) as db:
                result = await db.query("SELECT * FROM users")
            # Resource automatically shut down here
            ```

        Raises:
            InitializationError: If resource initialization fails
        """
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit asynchronous context manager, shutting down the resource.

        Automatically shuts down the resource when exiting an 'async with' block,
        ensuring proper cleanup even if exceptions occur within the context.

        Args:
            exc_type: Exception type if exception occurred, None otherwise
            exc_val: Exception instance if exception occurred, None otherwise
            exc_tb: Exception traceback if exception occurred, None otherwise

        Notes:
            - Shutdown occurs regardless of whether exceptions happened
            - Shutdown exceptions are logged but don't suppress original exceptions
            - Ensures resources are always cleaned up properly
            - Handles async shutdown gracefully
        """
        await self.shutdown()
