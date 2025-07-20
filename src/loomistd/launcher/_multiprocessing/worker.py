"""
Subprocess worker implementation for multiprocessing launcher.

This module contains the worker function that runs within subprocess
to manage host/server lifecycle and communicate with the parent process.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import signal
import threading
import time
import traceback
from multiprocessing.synchronize import Event as mpEventType
from typing import Any, cast

from loomicore.spec import ProxySpec, ResourceSpec, Spec

from .exceptions import MultiprocessingLauncherError
from .logger import logger
from .types import StartupResult, StartupStatus

__all__ = [
    "subprocess_worker_main",
]


def subprocess_worker_main(
    host_spec: Spec,
    ready_queue: mp.Queue,
    shutdown_event: mpEventType,
    worker_id: str | None = None,
) -> None:
    """
    Main function for subprocess worker.

    This function runs within the subprocess and manages the complete lifecycle
    of a host/server using the standard pattern:

        with host_spec.factory(host_spec) as server:
            server.start()  # blocking until shutdown

    Since server.start() is blocking, we run it in a background thread while
    the main thread monitors the shutdown_event. When shutdown is requested,
    we call server.shutdown() to gracefully stop the blocking start() call.

    Args:
        host_spec: Specification for the host/server to run
        ready_queue: Queue for sending startup results to parent
        shutdown_event: Event for receiving shutdown signals from parent
        worker_id: Optional identifier for this worker process
    """

    # Process setup
    pid = os.getpid()
    worker_name = worker_id or f"worker-{pid}"

    logger.info(f"[{worker_name}] Starting subprocess worker (PID: {pid})")
    logger.debug(f"[{worker_name}] Host spec: {host_spec}")

    # Set up signal handling for emergency shutdown
    _setup_signal_handling(worker_name)

    startup_signaled = False

    if isinstance(host_spec, ProxySpec):
        error_msg = "ProxySpec is not supported in subprocess workers"
        logger.error(f"[{worker_name}] {error_msg}")
        _signal_startup_error(ready_queue, worker_name, pid, error_msg)
        return

    # FIXME: Add proxyspec support, once resource factory runtime module is fixed

    host_spec = cast(ResourceSpec, host_spec)

    try:
        logger.info(f"[{worker_name}] Creating server from spec: {host_spec.name}")

        # Server lifecycle with context management
        with host_spec.factory(host_spec) as server:
            logger.info(f"[{worker_name}] Server context entered, ready to start")

            # Signal readiness to parent - server is created and initialized
            _signal_startup_success(ready_queue, worker_name, pid)
            startup_signaled = True

            # Run server with shutdown monitoring
            _run_server_with_shutdown_monitoring(server, worker_name, shutdown_event)

            logger.info(f"[{worker_name}] Server stopped")

    except Exception as e:
        error_msg = f"Worker error: {e}"
        logger.error(f"[{worker_name}] {error_msg}")
        logger.debug(f"[{worker_name}] Error traceback:\n{traceback.format_exc()}")

        # Signal error to parent if startup hasn't been signaled yet
        if not startup_signaled:
            _signal_startup_error(ready_queue, worker_name, pid, error_msg)

    finally:
        logger.info(f"[{worker_name}] Subprocess worker exiting")


def _setup_signal_handling(worker_name: str) -> None:
    """
    Set up signal handlers for emergency shutdown.

    Args:
        worker_name: Worker identifier for logging
    """

    def signal_handler(signum: int, frame: Any) -> None:
        signal_name = "SIGTERM" if signum == signal.SIGTERM else f"Signal-{signum}"
        logger.warning(f"[{worker_name}] Received {signal_name}, forcing exit")
        os._exit(1)  # Emergency exit

    # Set up handlers for emergency shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.debug(f"[{worker_name}] Signal handlers configured")


def _run_server_with_shutdown_monitoring(
    server: Any, worker_name: str, shutdown_event: mpEventType
) -> None:
    """
    Run the blocking server in a background thread while monitoring shutdown event.

    Args:
        server: Server instance with start() and shutdown() methods
        worker_name: Worker identifier for logging
        shutdown_event: Event that signals shutdown request
    """
    server_exception = None

    def server_thread_target():
        nonlocal server_exception
        try:
            logger.info(f"[{worker_name}] Starting server (blocking)...")
            server.start()
            logger.info(f"[{worker_name}] Server start() returned normally")
        except Exception as e:
            logger.error(f"[{worker_name}] Server start() raised exception: {e}")
            server_exception = e

    # Start server in background thread
    server_thread = threading.Thread(target=server_thread_target, daemon=False)
    server_thread.start()

    logger.info(f"[{worker_name}] Server thread started, monitoring for shutdown...")

    # Monitor shutdown event and server thread
    while True:
        # Check if shutdown requested
        if shutdown_event.is_set():
            logger.info(f"[{worker_name}] Shutdown requested, stopping server...")
            try:
                server.shutdown()
                logger.info(f"[{worker_name}] Server shutdown() called")
            except Exception as e:
                logger.error(f"[{worker_name}] Error calling server.shutdown(): {e}")
            break

        # Check if server thread finished
        if not server_thread.is_alive():
            logger.info(f"[{worker_name}] Server thread finished")
            break

        # Brief sleep to avoid busy waiting
        time.sleep(0.1)

    # Wait for server thread to finish
    logger.debug(f"[{worker_name}] Waiting for server thread to complete...")
    server_thread.join(timeout=10.0)

    if server_thread.is_alive():
        logger.warning(f"[{worker_name}] Server thread didn't exit within timeout")

    # Re-raise any server exception
    if server_exception:
        raise server_exception


def _signal_startup_success(ready_queue: mp.Queue, worker_name: str, pid: int) -> None:
    """
    Signal successful startup to parent process.

    Args:
        ready_queue: Queue for sending startup results
        worker_name: Worker identifier for logging
        pid: Process ID

    Raises:
        IPCError: If signaling fails
    """
    startup_result = StartupResult(
        status=StartupStatus.SUCCESS,
        connection_info={},  # Connection info handled by launcher/proxy
        error_message=None,
        pid=pid,
    )

    try:
        ready_queue.put(startup_result, timeout=5.0)
        logger.info(f"[{worker_name}] Startup success signaled to parent")

    except Exception as e:
        error_msg = f"Failed to signal startup success: {e}"
        logger.error(f"[{worker_name}] {error_msg}")
        raise MultiprocessingLauncherError(error_msg) from e


def _signal_startup_error(
    ready_queue: mp.Queue, worker_name: str, pid: int, error_message: str
) -> None:
    """
    Signal startup error to parent process.

    Args:
        ready_queue: Queue for sending startup results
        worker_name: Worker identifier for logging
        pid: Process ID
        error_message: Error description
    """
    error_result = StartupResult(
        status=StartupStatus.ERROR,
        connection_info=None,
        error_message=error_message,
        pid=pid,
    )

    try:
        ready_queue.put(error_result, timeout=2.0)
        logger.info(f"[{worker_name}] Startup error signaled to parent")

    except Exception as queue_error:
        logger.error(f"[{worker_name}] Failed to signal error to parent: {queue_error}")
        # Don't raise here - we're already in error handling
