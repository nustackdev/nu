"""
SyncResource - synchronous resource implementation.

This module provides the SyncResource class for building synchronous services
with automatic dependency injection and lifecycle management. SyncResource
provides a clean, declarative interface while delegating all operational
complexity to the runtime system.

Features:
- Declarative dependency injection via Attach descriptors
- Automatic lifecycle management (initialize/shutdown)
- Context manager support for resource cleanup
- User-overridable setup/cleanup hooks
- Thread-safe operations through runtime delegation

The class maintains the separation between user interface and implementation
by providing intuitive methods that delegate to the runtime system for
all complex operations.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from .base import BaseResource
from .meta import ResourceMeta

__all__ = [
    "SyncResource",
]


class SyncResource(BaseResource, metaclass=ResourceMeta):
    """
    Synchronous resource with lifecycle management and dependency injection.

    SyncResource provides the foundation for building synchronous services
    with automatic dependency management. It combines a clean, declarative
    interface with powerful runtime capabilities through delegation.

    Key Features:
        - Automatic dependency injection via Attach descriptors
        - Lifecycle management with user-overridable hooks
        - Context manager support for automatic cleanup
        - Thread-safe operations through runtime coordination
        - Resource deduplication based on specifications

    Usage Pattern:
        ```python
        class DatabaseService(SyncResource):
            cache = Attach(CacheSpec())
            connection_pool = Attach(ConnectionPoolSpec())

            def setup(self):
                # Dependencies automatically resolved and available
                self.connection_pool.connect()
                self.cache.initialize()

            def cleanup(self):
                self.connection_pool.disconnect()
                self.cache.shutdown()

            def query(self, sql: str):
                # Use dependencies in business logic
                result = self.connection_pool.execute(sql)
                self.cache.store(sql, result)
                return result

        # Simple usage with automatic lifecycle
        with DatabaseService(spec) as db:
            result = db.query("SELECT * FROM users")
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
        - User hooks (setup/cleanup) for resource-specific logic
        - Context manager ensures proper cleanup even on exceptions
    """

    # === Lifecycle Methods ===

    def initialize(self) -> None:
        """
        Initialize the resource and all its dependencies.

        This method handles the complete initialization process:
        1. Validates resource state and prerequisites
        2. Resolves and initializes all Attach descriptors
        3. Initializes dependencies in proper order
        4. Calls user-defined setup() method
        5. Updates resource state to INITIALIZED

        The method is idempotent - calling it on an already initialized
        resource is safe and will not cause duplicate initialization.

        Raises:
            InitializationError: If initialization fails at any step
            DependencyError: If dependency resolution or initialization fails
            StateError: If resource is in invalid state for initialization

        Notes:
            - All complexity handled by runtime system
            - User logic should go in setup() method, not here
            - Thread-safe through runtime coordination
            - Automatic dependency ordering prevents circular dependencies
        """
        from loomicore.runtime import get_lifecycle_manager

        get_lifecycle_manager().initialize_resource(self)

    def shutdown(self) -> None:
        """
        Shutdown the resource and clean up all dependencies.

        This method handles the complete shutdown process:
        1. Validates resource state and shutdown prerequisites
        2. Calls user-defined cleanup() method
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
            - User logic should go in cleanup() method, not here
            - Thread-safe through runtime coordination
            - Smart dependency cleanup prevents resource leaks
        """
        from loomicore.runtime import get_lifecycle_manager

        get_lifecycle_manager().shutdown_resource(self)

    # === User-Overridable Hooks ===

    def setup(self) -> None:
        """
        Resource-specific setup logic called during initialization.

        This method is called by the runtime after all dependencies have
        been resolved and initialized. Override this method to implement
        resource-specific initialization logic such as:
        - Opening connections or files
        - Configuring internal state
        - Setting up caches or pools
        - Registering callbacks or handlers

        When this method is called:
        - All Attach descriptors have been resolved to actual resources
        - All dependencies are fully initialized and ready for use
        - Resource is in INITIALIZING state

        Example:
            ```python
            def setup(self):
                # Dependencies are available and initialized
                self.database.connect()
                self.cache.warm_up()
                self.metrics.start_collection()
            ```

        Notes:
            - Called automatically by runtime during initialization
            - Dependencies guaranteed to be available and initialized
            - Exceptions will abort initialization and set ERROR state
            - Keep this method focused on setup, not business logic
        """
        pass

    def cleanup(self) -> None:
        """
        Resource-specific cleanup logic called during shutdown.

        This method is called by the runtime before dependencies are
        shut down. Override this method to implement resource-specific
        cleanup logic such as:
        - Closing connections or files
        - Flushing caches or buffers
        - Saving state or data
        - Unregistering callbacks or handlers

        When this method is called:
        - Resource is in SHUTTING_DOWN state
        - Dependencies are still available and operational
        - Shutdown process has been initiated

        Example:
            ```python
            def cleanup(self):
                # Dependencies still available for final operations
                self.cache.flush()
                self.database.save_pending_data()
                self.metrics.stop_collection()
            ```

        Notes:
            - Called automatically by runtime during shutdown
            - Dependencies still available for final operations
            - Exceptions logged but don't prevent shutdown completion
            - Keep this method focused on cleanup, not business logic
        """
        pass

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook called before resource initialization begins.

        This method is called by the runtime before any initialization logic
        starts. Override this method to implement validation, preparation, or
        setup logic that must happen before dependencies are resolved.

        When this method is called:
        - Resource is in CREATED state
        - No dependencies have been resolved yet
        - No initialization has occurred
        - Resource state validation has not yet happened

        Common use cases:
        - Validate configuration or environment
        - Prepare external resources or connections
        - Set up logging or monitoring
        - Perform security checks

        Example:
            ```python
            def pre_initialize(self):
                # Validate configuration before proceeding
                if not self.spec.database_url:
                    raise ValueError("Database URL required")
                # Prepare external state
                self._ensure_database_exists()
            ```

        Raises:
            InitializationError: If pre-initialization checks fail

        Notes:
            - Called before dependency resolution
            - Exceptions will abort initialization
            - Use for validation and preparation logic
            - Keep focused on prerequisites, not main setup
        """
        pass

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook called before resource shutdown begins.

        This method is called by the runtime before any shutdown logic
        starts. Override this method to implement preparation logic that
        must happen before the main cleanup begins.

        When this method is called:
        - Resource is in INITIALIZED state
        - All dependencies are still available and operational
        - No shutdown logic has started yet
        - Resource is still fully functional

        Common use cases:
        - Save critical state or data
        - Notify clients of impending shutdown
        - Gracefully finish in-progress operations
        - Prepare for clean shutdown

        Example:
            ```python
            def pre_shutdown(self):
                # Notify clients of shutdown
                self.broadcast_shutdown_notice()
                # Finish pending operations
                self.complete_pending_requests()
                # Save critical state
                self.save_checkpoint()
            ```

        Raises:
            ShutdownError: If pre-shutdown logic fails

        Notes:
            - Called before main cleanup begins
            - Dependencies still fully available
            - Use for graceful shutdown preparation
            - Exceptions will be logged but won't prevent shutdown
        """
        pass

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook called after resource shutdown completes.

        This method is called by the runtime after all shutdown logic
        has completed. Override this method to implement finalization
        logic that should happen after the resource is fully shut down.

        When this method is called:
        - Resource is in SHUTDOWN state
        - All dependencies have been shut down
        - User cleanup() method has completed
        - Resource is no longer operational

        Common use cases:
        - Unregister from external services
        - Clean up temporary files or resources
        - Emit shutdown events or notifications
        - Perform final cleanup tasks

        Example:
            ```python
            def post_shutdown(self):
                # Unregister from service discovery
                self.service_registry.unregister(self.name)
                # Clean up temp files
                self.cleanup_temp_files()
                # Log shutdown completion
                self.logger.info("Service shutdown complete")
            ```

        Raises:
            ShutdownError: If post-shutdown logic fails

        Notes:
            - Called after all shutdown is complete
            - Dependencies no longer available
            - Exceptions logged but don't affect shutdown status
            - Use for final cleanup and unregistration
        """
        pass

    def post_initialize(self) -> None:
        """
        Post-initialization hook called after resource initialization completes.

        This method is called by the runtime after all initialization logic
        has completed successfully. Override this method to implement
        finalization, registration, or startup logic that should happen
        after the resource is fully operational.

        When this method is called:
        - Resource is in INITIALIZED state
        - All dependencies are resolved and initialized
        - User setup() method has completed
        - Resource is fully operational

        Common use cases:
        - Register with external services
        - Start background tasks or workers
        - Emit startup events or notifications
        - Perform health checks or warming

        Example:
            ```python
            def post_initialize(self):
                # Register with service discovery
                self.service_registry.register(self.name, self.endpoint)
                # Start background maintenance tasks
                self.start_background_workers()
            ```

        Raises:
            InitializationError: If post-initialization logic fails

        Notes:
            - Called after all initialization is complete
            - Resource is fully operational when this runs
            - Exceptions will mark resource as ERROR state
            - Use for finalization and registration logic
        """
        pass

    # === Context Manager Support ===

    def __enter__(self) -> Self:
        """
        Enter synchronous context manager, initializing the resource.

        Automatically initializes the resource when entering a 'with' block,
        ensuring it's ready for use within the context.

        Returns:
            Self for use within the context block

        Example:
            ```python
            with DatabaseService(spec) as db:
                result = db.query("SELECT * FROM users")
            # Resource automatically shut down here
            ```

        Raises:
            InitializationError: If resource initialization fails
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit synchronous context manager, shutting down the resource.

        Automatically shuts down the resource when exiting a 'with' block,
        ensuring proper cleanup even if exceptions occur within the context.

        Args:
            exc_type: Exception type if exception occurred, None otherwise
            exc_val: Exception instance if exception occurred, None otherwise
            exc_tb: Exception traceback if exception occurred, None otherwise

        Notes:
            - Shutdown occurs regardless of whether exceptions happened
            - Shutdown exceptions are logged but don't suppress original exceptions
            - Ensures resources are always cleaned up properly
        """
        self.shutdown()
