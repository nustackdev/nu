"""
Multiprocessing launcher implementation.

This module provides the main MultiprocessingLauncher class that creates
and manages subprocesses running host servers, along with its specification.
"""

from __future__ import annotations

import multiprocessing as mp
import queue
import time
from multiprocessing.synchronize import Event as mpEventType
from typing import Optional

import attrs
from frozendict import frozendict

from loomicore.spec import ResourceSpec, Spec

from ..base import BaseLauncher
from .exceptions import (
    ProcessCreationError,
    ProcessStartupError,
    ProcessTerminationError,
    ProcessTimeoutError,
)
from .logger import logger
from .types import StartupResult, StartupStatus
from .worker import subprocess_worker_main

__all__ = [
    "MultiprocessingLauncher",
    "MultiprocessingLauncherSpec",
]


class MultiprocessingLauncher(BaseLauncher):
    """
    Multiprocessing launcher that provisions subprocess infrastructure.

    This launcher creates and manages subprocesses that run host servers.
    It follows the standard launcher lifecycle:

    1. Infrastructure provisioning: Creates subprocess and IPC primitives
    2. Host startup: Starts subprocess and waits for server readiness
    3. Connection info: Provides connection details for proxy clients
    4. Graceful shutdown: Stops server and cleans up subprocess

    The launcher supports any host spec that can run in a subprocess,
    commonly RPyC servers (TCP or Unix socket) but extensible to other
    server types.

    Examples:
        Basic usage with Unix socket:
        >>> from loomistd.rpc.rpyc import RPyCUnixServerSpec
        >>> spec = MultiprocessingLauncherSpec(
        ...     host=RPyCUnixServerSpec(socket_path="/tmp/service.sock")
        ... )
        >>> with MultiprocessingLauncher(spec) as launcher:
        ...     connection_info = launcher.get_connection_info()
        ...     # Clients can now connect using connection_info

        With custom timeouts:
        >>> spec = MultiprocessingLauncherSpec(
        ...     host=RPyCTCPServerSpec(host="localhost", port=18861),
        ...     startup_timeout=15.0,
        ...     process_timeout=60.0
        ... )
        >>> launcher = MultiprocessingLauncher(spec)
        >>> launcher.setup()
        >>> # ... use launcher ...
        >>> launcher.cleanup()
    """

    spec: MultiprocessingLauncherSpec

    def __init__(self, spec: MultiprocessingLauncherSpec):
        """
        Initialize multiprocessing launcher.

        Args:
            spec: Launcher specification including host and process config
        """
        super().__init__(spec)

        # Process management
        self._process: mp.Process | None = None
        self._worker_id: str | None = None

        # IPC primitives for subprocess communication
        self._ready_queue: mp.Queue | None = None
        self._shutdown_event: mpEventType | None = None

        # Connection information for clients
        self._connection_info: dict | None = None

        logger.debug(f"Initialized with host: {spec.host}")

    def _provision_infrastructure(self) -> None:
        """
        Provision subprocess infrastructure.

        Creates IPC primitives (queue and event) and subprocess instance
        but does not start the subprocess yet. The subprocess will be
        started in _start_host().

        Raises:
            ProcessCreationError: If infrastructure provisioning fails
        """
        logger.info("Provisioning subprocess infrastructure...")

        try:
            # Create IPC primitives for subprocess communication
            self._ready_queue = mp.Queue()
            self._shutdown_event = mp.Event()

            # Generate worker identifier
            self._worker_id = f"mp-worker-{int(time.time() * 1000) % 100000}"

            # Create subprocess (but don't start yet)
            self._process = mp.Process(
                target=subprocess_worker_main,
                args=(self.spec.host, self._ready_queue, self._shutdown_event, self._worker_id),
                name=self._worker_id,
                daemon=False,  # Explicit lifecycle management
            )

            logger.info(f"Infrastructure provisioned (worker: {self._worker_id})")

        except Exception as e:
            logger.error(f"Failed to provision infrastructure: {e}")
            raise ProcessCreationError(f"Failed to provision subprocess infrastructure: {e}") from e

    def _start_host(self) -> None:
        """
        Start subprocess and wait for host readiness.

        Starts the subprocess, waits for the server to start up within
        the subprocess, and retrieves connection information for clients.

        Raises:
            ProcessStartupError: If subprocess startup fails
            ProcessTimeoutError: If startup exceeds timeout
            IPCError: If communication with subprocess fails
        """
        if not self._process or not self._ready_queue:
            raise ProcessStartupError("Infrastructure not provisioned")

        logger.info(f"Starting subprocess worker: {self._worker_id}")

        try:
            # Start the subprocess
            self._process.start()
            actual_pid = self._process.pid

            logger.info(f"Subprocess started (PID: {actual_pid})")

            # Wait for startup result from subprocess
            logger.info(f"Waiting for host startup (timeout: {self.spec.startup_timeout}s)...")

            try:
                startup_result: StartupResult = self._ready_queue.get(
                    timeout=self.spec.startup_timeout
                )

            except queue.Empty:
                # Startup timeout - check if process is still alive
                if self._process.is_alive():
                    error_msg = f"Host startup timeout after {self.spec.startup_timeout}s (process still running)"
                else:
                    error_msg = f"Process died during startup (exit code: {self._process.exitcode})"

                logger.error(error_msg)
                raise ProcessTimeoutError(error_msg)

            # Process startup result
            if startup_result.status == StartupStatus.SUCCESS:
                self._connection_info = startup_result.connection_info
                logger.info("Host startup successful!")
                logger.debug(f"Connection info: {self._connection_info}")

            elif startup_result.status == StartupStatus.ERROR:
                error_msg = startup_result.error_message or "Unknown startup error"
                logger.error(f"Host startup failed: {error_msg}")
                raise ProcessStartupError(f"Host startup failed: {error_msg}")

            else:
                unexpected_status = startup_result.status
                logger.error(f"Unexpected startup status: {unexpected_status}")
                raise ProcessStartupError(f"Unexpected startup status: {unexpected_status}")

        except (ProcessStartupError, ProcessTimeoutError):
            # Re-raise specific errors
            raise

        except Exception as e:
            logger.error(f"Unexpected error during host startup: {e}")
            raise ProcessStartupError(f"Unexpected startup error: {e}") from e

    def _stop_host(self) -> None:
        """
        Signal subprocess to stop the host gracefully.

        Sends shutdown signal to subprocess via shared event.
        The actual process termination is handled in _cleanup_infrastructure().
        """
        if self._shutdown_event:
            logger.info(f"Signaling host shutdown to worker: {self._worker_id}")
            self._shutdown_event.set()
        else:
            logger.warning("No shutdown event available for signaling")

    def _cleanup_infrastructure(self) -> None:
        """
        Cleanup subprocess infrastructure.

        Terminates subprocess with escalating force (graceful -> terminate -> kill)
        and cleans up IPC resources.

        Raises:
            ProcessTerminationError: If subprocess cleanup fails completely
        """
        if not self._process:
            logger.debug("No process to cleanup")
            return

        process_pid = self._process.pid
        logger.info(f"Cleaning up subprocess {process_pid}...")

        cleanup_successful = False

        try:
            # Step 1: Wait for graceful shutdown
            if self._process.is_alive():
                logger.debug("Waiting for graceful shutdown...")
                self._process.join(timeout=min(10.0, self.spec.process_timeout / 2))

            # Step 2: Terminate if still alive
            if self._process.is_alive():
                logger.info("Process still alive, terminating...")
                self._process.terminate()
                self._process.join(timeout=5.0)

            # Step 3: Kill if still alive
            if self._process.is_alive():
                logger.warning("Process didn't terminate, killing...")
                self._process.kill()
                self._process.join(timeout=2.0)

            # Step 4: Check final state
            if self._process.is_alive():
                logger.error(f"Failed to kill process {process_pid}")
                raise ProcessTerminationError(f"Failed to terminate subprocess {process_pid}")
            else:
                exit_code = self._process.exitcode
                logger.info(f"Process {process_pid} terminated (exit code: {exit_code})")
                cleanup_successful = True

        except Exception as e:
            logger.error(f"Error during subprocess cleanup: {e}")
            if not cleanup_successful:
                raise ProcessTerminationError(f"Subprocess cleanup failed: {e}") from e

        finally:
            # Clean up references regardless of success/failure
            self._process = None
            self._ready_queue = None
            self._shutdown_event = None
            self._connection_info = None
            self._worker_id = None

            logger.info("Infrastructure cleanup completed")

    def get_connection_info(self) -> dict:
        """
        Get connection information for proxy clients.

        Returns connection details that proxy clients can use to connect
        to the host server running in the subprocess.

        Returns:
            Dictionary containing connection information (host, port, socket_path, etc.)

        Raises:
            RuntimeError: If launcher is not ready or connection info unavailable
        """
        if not self.is_ready:
            raise RuntimeError("Launcher not ready - call setup() first")

        if not self._connection_info:
            raise RuntimeError("Connection information not available")

        # Return copy to prevent modification
        return self._connection_info.copy()

    @property
    def is_ready(self) -> bool:
        """
        Check if launcher and host are ready for client connections.

        Returns:
            True if infrastructure is provisioned, host is started,
            connection info is available, and subprocess is alive
        """
        return (
            self._infrastructure_ready
            and self._host_started
            and self._connection_info is not None
            and self._process is not None
            and self._process.is_alive()
        )

    @property
    def process_id(self) -> Optional[int]:
        """Get subprocess PID if available."""
        return self._process.pid if self._process else None

    @property
    def worker_id(self) -> Optional[str]:
        """Get worker identifier if available."""
        return self._worker_id


@attrs.define(frozen=True, slots=True, kw_only=True)
class MultiprocessingLauncherSpec(ResourceSpec):
    """
    Specification for multiprocessing launcher configuration.

    This specification defines how to configure a multiprocessing launcher,
    including the host server to run within the subprocess and process
    management settings like timeouts and resource limits.

    The launcher creates a subprocess and runs the specified host (server)
    within that subprocess. The host can be any compatible server spec,
    most commonly RPyC servers (TCP or Unix socket).

    Attributes:
        name: Launcher name for identification
        factory: Launcher class (MultiprocessingLauncher)
        host: Specification for the host/server to run in subprocess
        startup_timeout: Maximum time to wait for server startup (seconds)
        process_timeout: Maximum time to wait for process operations (seconds)
        config: Additional process-specific configuration options

    Examples:
        Unix socket RPyC server:
        >>> from loomistd.rpc.rpyc import RPyCUnixServerSpec
        >>> spec = MultiprocessingLauncherSpec(
        ...     host=RPyCUnixServerSpec(socket_path="/tmp/service.sock"),
        ...     startup_timeout=10.0
        ... )

        TCP RPyC server:
        >>> from loomistd.rpc.rpyc import RPyCTCPServerSpec
        >>> spec = MultiprocessingLauncherSpec(
        ...     host=RPyCTCPServerSpec(host="localhost", port=18861),
        ...     startup_timeout=15.0,
        ...     process_timeout=60.0
        ... )

        With custom process configuration:
        >>> spec = MultiprocessingLauncherSpec(
        ...     host=RPyCUnixServerSpec(socket_path="/tmp/service.sock"),
        ...     config={"daemon": False, "name": "loomi_worker"}
        ... )
    """

    name: str = "multiprocessing_launcher"
    factory: type = MultiprocessingLauncher

    # Host specification for the server to run in subprocess
    host: Spec

    # Process timing configuration
    startup_timeout: float = 30.0
    """Maximum time (seconds) to wait for host startup within subprocess."""

    process_timeout: float = 60.0
    """Maximum time (seconds) to wait for process lifecycle operations."""

    # Process configuration
    config: frozendict = attrs.field(factory=frozendict)
    """Additional configuration options for subprocess creation and management."""
