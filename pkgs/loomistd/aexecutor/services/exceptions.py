class TaskExecutionException(Exception):
    """Base class for exceptions in this module."""

    pass


class TaskExecutionCancelledError(TaskExecutionException):
    """Exception raised when a task execution is cancelled."""

    pass


class TaskExecutionTimeoutError(TaskExecutionException):
    """Exception raised when a task execution times out."""

    pass
