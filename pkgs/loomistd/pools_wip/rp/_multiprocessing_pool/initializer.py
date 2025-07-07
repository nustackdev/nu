from loomi.spec import Spec

from .logger import logger


def worker_server_initializer(server_spec: Spec) -> None:
    """
    Worker function that runs in each multiprocessing process.

    Creates and starts a Loomi server at the specified endpoint.
    This function runs indefinitely until the process is terminated.

    Args:
        endpoint: Worker endpoint configuration
    """
    try:
        logger.info(f"Starting worker server with Spec: {server_spec}")

        with server_spec.factory(server_spec) as server:
            logger.info("Worker server initialized, starting...")

            # Start the server - this blocks until process is terminated
            server.start()

    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        raise
