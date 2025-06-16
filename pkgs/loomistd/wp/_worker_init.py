"""Worker initialization utilities."""

from __future__ import annotations

import atexit
from typing import Any, Callable

from ._types import WorkerCleanupFunction, WorkerInitFunction

__all__ = [
    "create_worker_initializer",
    "create_worker_wrapper",
]

# Global storage for worker cleanup function
_worker_cleanup_func: WorkerCleanupFunction | None = None
_worker_cleanup_args: tuple[Any, ...] = ()
_worker_cleanup_kwargs: dict[str, Any] = {}


def _worker_cleanup() -> None:
    """Internal cleanup function called on worker exit."""
    if _worker_cleanup_func is not None:
        try:
            _worker_cleanup_func(*_worker_cleanup_args, **_worker_cleanup_kwargs)
        except Exception:
            # Ignore cleanup errors to avoid breaking worker shutdown
            pass


class WorkerInitializer:
    """Picklable worker initializer."""

    def __init__(
        self,
        init_func: WorkerInitFunction | None = None,
        init_args: tuple[Any, ...] | None = None,
        init_kwargs: dict[str, Any] | None = None,
        cleanup_func: WorkerCleanupFunction | None = None,
        cleanup_args: tuple[Any, ...] | None = None,
        cleanup_kwargs: dict[str, Any] | None = None,
    ):
        self.init_func = init_func
        self.init_args = init_args or ()
        self.init_kwargs = init_kwargs or {}
        self.cleanup_func = cleanup_func
        self.cleanup_args = cleanup_args or ()
        self.cleanup_kwargs = cleanup_kwargs or {}

    def __call__(self) -> None:
        """Initialize worker process."""
        global _worker_cleanup_func, _worker_cleanup_args, _worker_cleanup_kwargs

        # Set up cleanup function if provided
        if self.cleanup_func is not None:
            _worker_cleanup_func = self.cleanup_func
            _worker_cleanup_args = self.cleanup_args
            _worker_cleanup_kwargs = self.cleanup_kwargs
            atexit.register(_worker_cleanup)

        # Call initialization function if provided
        if self.init_func is not None:
            self.init_func(*self.init_args, **self.init_kwargs)


def create_worker_initializer(
    init_func: WorkerInitFunction | None = None,
    init_args: tuple[Any, ...] | None = None,
    init_kwargs: dict[str, Any] | None = None,
    cleanup_func: WorkerCleanupFunction | None = None,
    cleanup_args: tuple[Any, ...] | None = None,
    cleanup_kwargs: dict[str, Any] | None = None,
) -> WorkerInitializer | None:
    """
    Create a worker initializer function for multiprocessing pools.

    Returns:
        Initializer callable to pass to ProcessPoolExecutor, or None if no initialization needed
    """
    if init_func is None and cleanup_func is None:
        return None

    return WorkerInitializer(
        init_func=init_func,
        init_args=init_args,
        init_kwargs=init_kwargs,
        cleanup_func=cleanup_func,
        cleanup_args=cleanup_args,
        cleanup_kwargs=cleanup_kwargs,
    )


def create_worker_wrapper(
    func: Callable[..., Any],
    init_func: WorkerInitFunction | None = None,
    init_args: tuple[Any, ...] | None = None,
    init_kwargs: dict[str, Any] | None = None,
) -> Callable[..., Any]:
    """
    Create a wrapper function that initializes the worker before executing the task.

    This is an alternative approach for cases where the executor doesn't support
    initializer functions.

    Args:
        func: The original function to execute
        init_func: Function to call for worker initialization
        init_args: Arguments to pass to init_func
        init_kwargs: Keyword arguments to pass to init_func

    Returns:
        Wrapped function that performs initialization before execution
    """
    if init_func is None:
        return func

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper that initializes worker then executes function."""
        # Initialize worker (this will be called once per worker process)
        init_func(*(init_args or ()), **(init_kwargs or {}))

        # Execute the original function
        return func(*args, **kwargs)

    return wrapper
