from enum import Enum, auto


class ErrorBehavior(Enum):
    """
    Defines how operations should handle errors.

    This enum specifies the different strategies for error handling
    that operations can use.
    """

    FAIL = auto()
    """
    Stop execution and propagate the error (default).

    When an operation encounters an error with this behavior,
    execution stops and the error is propagated to the caller.
    """

    CONTINUE = auto()
    """
    Log the error but continue execution.

    When an operation encounters an error with this behavior,
    it logs the error but continues execution, returning None
    or a default value.
    """

    RETRY = auto()
    """
    Attempt to retry the failed operation.

    When an operation encounters an error with this behavior,
    it will attempt to retry the operation according to the
    configured retry policy.
    """
