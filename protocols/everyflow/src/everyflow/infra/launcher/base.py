"""Base launcher implementation providing common functionality.

This module provides the BaseLauncher class that implements common patterns
for launcher implementations. Launchers provision infrastructure and start
hosts that can serve multiple resources when proxies connect to them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import final

import attrs
from everylink import ResourceSpec, Spec, SyncResource


__all__ = [
    "BaseLauncher",
]


logger = getLogger(__name__)


class BaseLauncher(SyncResource, ABC):
    """Base launcher implementation providing common functionality.

    Launchers provision infrastructure (processes, containers, Ray actors) and
    start hosts (servers) within that infrastructure. The hosts can then serve
    multiple resources when proxies connect to them using the connection
    information from the launcher specification.

    Subclasses must implement:
    - _provision_infrastructure(): Infrastructure provisioning logic
    - _start_host(): Host/server startup within provisioned infrastructure
    - _stop_host(): Host/server shutdown
    - _cleanup_infrastructure(): Infrastructure cleanup and deallocation

    The launcher automatically provisions infrastructure and starts the host
    during setup(), following standard EveryFlow resource patterns.

    Examples:
        >>> class ProcessLauncher(BaseLauncher):
        ...     def _provision_infrastructure(self) -> None:
        ...         self._process = multiprocessing.Process(target=self._run_in_process)
        ...         self._process.start()
        ...
        ...     def _start_host(self) -> None:
        ...         # Signal process to start RPyC server
        ...         self._start_rpyc_server()
        ...
        ...     def _stop_host(self) -> None:
        ...         # Signal process to stop RPyC server
        ...         self._stop_rpyc_server()
        ...
        ...     def _cleanup_infrastructure(self) -> None:
        ...         self._process.terminate()
        ...         self._process.join()
    """

    spec: BaseLauncherSpec

    @final
    def setup(self) -> None:
        """Setup the launcher - provision infrastructure and start host.

        This method automatically:
        1. Validates launcher configuration
        2. Provisions infrastructure (process, container, Ray actor, etc.)
        3. Starts the host/server within the infrastructure

        The host can then serve multiple resources when proxies connect using
        the connection information from the launcher specification.

        Raises:
            LauncherConfigurationError: If configuration is invalid
            LauncherProvisioningError: If infrastructure provisioning fails
            LauncherOperationError: If host startup fails
        """
        logger.info(f"Setting up launcher: {self.readable_name}")

        self._infrastructure_ready = False
        self._host_started = False

        try:
            # Provision infrastructure
            logger.debug(f"Provisioning infrastructure for {self.readable_name}")
            self._provision_infrastructure()
            self._infrastructure_ready = True
            logger.debug(f"Infrastructure provisioned for {self.readable_name}")

            # Start host/server within infrastructure
            logger.debug(f"Starting host for {self.readable_name}")
            self._start_host()
            self._host_started = True
            logger.debug(f"Host started for {self.readable_name}")

            logger.info(f"Successfully set up launcher: {self.readable_name}")

        except Exception as e:
            logger.error(f"Failed to setup launcher {self.readable_name}: {e}")
            # Cleanup partial state
            self._cleanup_partial_setup()
            raise

    @final
    def cleanup(self) -> None:
        """Clean up the launcher and all managed resources.

        Cleanup happens in reverse order of setup:
        1. Stop host/server
        2. Clean up infrastructure

        Each step is protected to ensure cleanup continues even if
        individual steps fail.
        """
        logger.info(f"Cleaning up launcher: {self.readable_name}")

        # Stop host first
        if self._host_started:
            try:
                logger.debug(f"Stopping host for {self.readable_name}")
                self._stop_host()
                logger.debug(f"Host stopped for {self.readable_name}")
            except Exception as e:
                logger.error(f"Error stopping host for {self.readable_name}: {e}")
            finally:
                self._host_started = False

        # Clean up infrastructure
        if self._infrastructure_ready:
            try:
                logger.debug(f"Cleaning up infrastructure for {self.readable_name}")
                self._cleanup_infrastructure()
                logger.debug(f"Infrastructure cleaned up for {self.readable_name}")
            except Exception as e:
                logger.error(f"Error cleaning up infrastructure for {self.readable_name}: {e}")
            finally:
                self._infrastructure_ready = False

        logger.info(f"Successfully cleaned up launcher: {self.readable_name}")

    # Abstract methods that subclasses must implement

    @abstractmethod
    def _provision_infrastructure(self) -> None:
        """Provision infrastructure for hosting the server.

        This method should handle infrastructure-specific provisioning
        such as starting processes, creating containers, or initializing
        Ray actors. The infrastructure should be ready to run the host
        when this method completes.

        Raises:
            LauncherProvisioningError: If infrastructure provisioning fails

        Examples:
            Process launcher:
            >>> def _provision_infrastructure(self) -> None:
            ...     self._process = multiprocessing.Process(target=self._run_server)
            ...     self._process.start()

            Container launcher:
            >>> def _provision_infrastructure(self) -> None:
            ...     self._container = docker_client.containers.run(
            ...         image="python:3.11", command="python server.py", detach=True
            ...     )
        """
        ...

    @abstractmethod
    def _start_host(self) -> None:
        """Start the host/server within the provisioned infrastructure.

        This method should start the host (RPyC server, Ray actor, HTTP server,
        etc.) within the already provisioned infrastructure. The host should
        be ready to accept connections when this method completes.

        Raises:
            LauncherOperationError: If host startup fails

        Examples:
            RPyC server startup:
            >>> def _start_host(self) -> None:
            ...     # Send signal to process to start RPyC server
            ...     self._start_signal.set()
            ...     # Wait for server to be ready
            ...     self._ready_signal.wait(timeout=30)

            Ray actor startup:
            >>> def _start_host(self) -> None:
            ...     # Ray actor is already running, just initialize server
            ...     ray.get(self._actor.start_server.remote())
        """
        ...

    @abstractmethod
    def _stop_host(self) -> None:
        """Stop the host/server.

        This method should gracefully stop the host/server while leaving
        the infrastructure intact. Called during cleanup before infrastructure
        is deallocated.

        Examples:
            RPyC server shutdown:
            >>> def _stop_host(self) -> None:
            ...     # Send signal to process to stop RPyC server
            ...     self._stop_signal.set()
            ...     # Wait for server to shutdown
            ...     self._stopped_signal.wait(timeout=30)

            Ray actor shutdown:
            >>> def _stop_host(self) -> None:
            ...     # Stop server in Ray actor
            ...     ray.get(self._actor.stop_server.remote())
        """
        ...

    @abstractmethod
    def _cleanup_infrastructure(self) -> None:
        """Clean up infrastructure and deallocate all resources.

        This method should clean up all infrastructure resources such as
        stopping processes, removing containers, or terminating Ray actors.
        Called after the host has been stopped.

        Examples:
            Process cleanup:
            >>> def _cleanup_infrastructure(self) -> None:
            ...     if self._process.is_alive():
            ...         self._process.terminate()
            ...         self._process.join(timeout=10)
            ...         if self._process.is_alive():
            ...             self._process.kill()

            Container cleanup:
            >>> def _cleanup_infrastructure(self) -> None:
            ...     self._container.stop()
            ...     self._container.remove()
        """
        ...

    # Private helper methods

    @final
    def _cleanup_partial_setup(self) -> None:
        """Clean up partial state after setup failure."""
        logger.debug(f"Cleaning up partial setup for {self.readable_name}")

        if self._host_started:
            try:
                self._stop_host()
            except Exception as e:
                logger.error(f"Error stopping host during partial cleanup: {e}")
            finally:
                self._host_started = False

        if self._infrastructure_ready:
            try:
                self._cleanup_infrastructure()
            except Exception as e:
                logger.error(f"Error cleaning up infrastructure during partial cleanup: {e}")
            finally:
                self._infrastructure_ready = False


@attrs.define(frozen=True, slots=True, kw_only=True)
class BaseLauncherSpec(ResourceSpec):
    """Base specification for launcher configuration.

    This specification defines how a launcher should be configured,
    including the target resource to launch, the host configuration,
    and launcher-specific settings.

    Attributes:
        name: Launcher name
        factory: Launcher class to instantiate
        resource_spec: Specification of the resource to be launched
        host_spec: Specification of the host that will serve the resource
        config: Launcher-specific configuration options

    Examples:
        Basic launcher specification:
        >>> spec = LauncherSpec(
        ...     name="process_launcher",
        ...     factory=MultiprocessingLauncher,
        ...     resource_spec=ComputeServiceSpec(),
        ...     host_spec=RPyCHostSpec(port=18812),
        ...     config={"timeout": 30},
        ... )

        Ray launcher specification:
        >>> spec = LauncherSpec(
        ...     name="ray_launcher",
        ...     factory=RayLauncher,
        ...     resource_spec=ComputeServiceSpec(),
        ...     host_spec=RayActorHostSpec(),
        ...     config={"cluster_address": "ray://head:10001"},
        ... )
    """

    # Host specification for serving the resource
    host: Spec
