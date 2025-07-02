from __future__ import annotations

import ray

from loomi.spec import Spec

from .logger import logger

__all__ = [
    "RayWorkerActor",
]


@ray.remote
class RayWorkerActor:
    """Ray actor that wraps a Loomi server."""

    def __init__(self, worker_index: int, server_spec: Spec):
        self.worker_index = worker_index
        self.server_spec = server_spec
        self.server = None
        self._initialize_server()

    def _initialize_server(self):
        """Initialize the Loomi server in this actor."""
        logger.info(f"Worker {self.worker_index} initializing server with spec: {self.server_spec}")

        try:
            # Create the server instance
            self.server = self.server_spec.factory(self.server_spec)

            self.server.initialize()

            logger.info(f"Worker {self.worker_index} server initialized")

        except Exception as e:
            logger.error(f"Worker {self.worker_index} failed to initialize: {e}")
            raise

    def start_server(self):
        """Start the server in this worker."""
        try:
            if self.server is None:
                raise RuntimeError("Server not initialized")

            # Start server in a separate thread so this method can return
            import threading

            self.server_thread = threading.Thread(target=self.server.start)
            self.server_thread.daemon = True
            self.server_thread.start()

            # Give it a moment to start up
            import time

            time.sleep(0.1)  # implement a proper readiness check

            # Connect/start the server
            logger.info(f"Worker {self.worker_index} server started")

            return {"status": "started", "worker_index": self.worker_index}

        except Exception as e:
            logger.error(f"Worker {self.worker_index} failed to start server: {e}")
            raise

    def stop_server(self):
        """Stop the server in this worker."""
        try:
            if self.server is not None:
                self.server.shutdown()
                logger.info(f"Worker {self.worker_index} server stopped")

            return {"status": "stopped", "worker_index": self.worker_index}

        except Exception as e:
            logger.error(f"Worker {self.worker_index} failed to stop server: {e}")
            raise

    def get_worker_info(self):
        """Get information about this worker."""
        return {
            "worker_index": self.worker_index,
            "server_connected": self.server.is_connected() if self.server else False,
            "server_spec": str(self.server_spec),
        }

    def health_check(self):
        """Check if this worker is healthy."""
        try:
            if self.server is None:
                return {"healthy": False, "reason": "server_not_initialized"}

            if not self.server.is_connected():
                return {"healthy": False, "reason": "server_not_connected"}

            # You can add more health checks here
            return {"healthy": True, "worker_index": self.worker_index}

        except Exception as e:
            return {"healthy": False, "reason": str(e)}
