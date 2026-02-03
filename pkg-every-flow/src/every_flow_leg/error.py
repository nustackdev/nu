"""Error handling flows.

This module provides flows for error handling and resilience:
- TryCatch: Execute with error recovery
- Retry: Retry on failure with backoff
- Assert: Validate conditions during execution
"""

from __future__ import annotations

import asyncio
import logging

import attrs

from everybase import Flow, Runtime, Term


__all__ = [
    "Assert",
    "Retry",
    "TryCatch",
]


# TODO: update once flow exceptions are there
class RetryExhaustedError(Exception):
    pass


logger = logging.getLogger(__name__)


@attrs.define
class _TryCatch[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child with error handling.

    Executes the main child flow. If it raises an exception,
    executes the catch handler. The finally handler always runs.

    The caught exception is available via runtime.attributes as "error".

    Flow Building Pattern:
        Flows are self-contained and cannot return values directly.
        Error information is passed via runtime.attributes:

        - "error": The exception message (str)
        - "error_type": The exception class name (str)

        Child flows can read these using runtime.attributes.get()
    """

    child: Flow | Term | None = attrs.field(default=None)
    catch: Flow | Term | None = attrs.field(default=None)
    finally_: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute with try/catch/finally semantics."""
        if self.child is None:
            raise ValueError("No child flow provided")

        caught_error: Exception | None = None

        try:
            await self.execute_child(self.child, 0, runtime)
        except Exception as e:
            caught_error = e
            logger.debug(f"TryCatch caught: {e}")

            if self.catch is not None:
                # Store error info for catch handler
                runtime.attributes.set(
                    runtime.path,
                    "error",
                    str(e),
                    step_name=self.name,
                )
                runtime.attributes.set(
                    runtime.path,
                    "error_type",
                    e.__class__.__name__,
                    step_name=self.name,
                )

                await self.execute_child(self.catch, "catch", runtime)
        finally:
            if self.finally_ is not None:
                await self.execute_child(self.finally_, "finally", runtime)

        # If catch handler wasn't provided, re-raise
        if caught_error is not None and self.catch is None:
            raise caught_error


@attrs.define
class _Retry[RuntimeT: Runtime](Flow[RuntimeT]):
    """Retry child on failure with configurable backoff.

    Attempts to execute the child flow up to max_attempts times.
    On failure, waits for delay (multiplied by backoff each attempt)
    before retrying.

    Flow Building Pattern:
        Current attempt number is available via runtime.attributes as "attempt".
        Child flows can use this for logging or conditional behavior.
    """

    child: Flow | Term | None = attrs.field(default=None)
    max_attempts: Term | int = attrs.field(default=3)
    delay: Term | float = attrs.field(default=0.0)
    backoff: Term | float = attrs.field(default=1.0)
    on_retry: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute with retry logic."""
        if self.child is None:
            raise ValueError("No child flow provided")

        # Resolve configuration
        max_attempts = self._resolve_int(runtime, self.max_attempts)
        delay = self._resolve_float(runtime, self.delay)
        backoff = self._resolve_float(runtime, self.backoff)

        last_error: Exception | None = None
        current_delay = delay

        for attempt in range(1, max_attempts + 1):
            runtime.cancellation.terminate_cancelled(runtime.path)

            # Store attempt number for child access
            runtime.attributes.set(
                runtime.path,
                "attempt",
                attempt,
                step_name=self.name,
            )

            try:
                await self.execute_child(self.child, 0, runtime)
                return  # Success
            except Exception as e:
                last_error = e
                logger.debug(f"Retry attempt {attempt}/{max_attempts} failed: {e}")

                if attempt < max_attempts:
                    # Execute on_retry handler if provided
                    if self.on_retry is not None:
                        runtime.attributes.set(
                            runtime.path,
                            "error",
                            str(e),
                            step_name=self.name,
                        )
                        await self.execute_child(self.on_retry, "on_retry", runtime)

                    # Wait before retry
                    if current_delay > 0:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

        # All attempts exhausted
        raise RetryExhaustedError(
            f"All {max_attempts} retry attempts exhausted",
            path=runtime.path,
            attempts=max_attempts,
            last_error=last_error,
        )

    def _resolve_int(self, runtime: RuntimeT, value: Term | int) -> int:
        """Resolve Term or int to int."""
        if isinstance(value, Term):
            result = runtime.terms.execute_term(value)
            if not isinstance(result, int):
                raise ValueError(f"Expected int, got {type(result)}")
            return result
        return value

    def _resolve_float(self, runtime: RuntimeT, value: Term | float) -> float:
        """Resolve Term or float to float."""
        if isinstance(value, Term):
            result = runtime.terms.execute_term(value)
            if not isinstance(result, (int, float)):
                raise ValueError(f"Expected float, got {type(result)}")
            return float(result)
        return value


@attrs.define
class _Assert[RuntimeT: Runtime](Flow[RuntimeT]):
    """Assert a condition, raising AssertionError if false.

    Evaluates the condition and raises AssertionError with the
    provided message if the condition is falsy.

    Useful for:
    - Validating preconditions before operations
    - Debugging flow state
    - Enforcing invariants
    """

    condition: Term | bool = attrs.field(default=True)
    message: str = attrs.field(default="Assertion failed")

    async def run(self, runtime: RuntimeT) -> None:
        """Check assertion."""
        if isinstance(self.condition, Term):
            condition = runtime.terms.execute_term(self.condition)
        else:
            condition = self.condition

        if not condition:
            raise AssertionError(self.message)


# =============================================================================
# Wrapper Functions
# =============================================================================


def TryCatch(  # noqa: N802
    child: Flow | Term,
    catch: Flow | Term | None = None,
    finally_: Flow | Term | None = None,
) -> _TryCatch:
    """Execute child with error handling.

    Executes the main child flow. If it raises an exception,
    executes the catch handler. The finally handler always runs.

    Error info available via runtime.attributes:
    - "error": The exception message
    - "error_type": The exception class name

    Args:
        child: Main flow to execute
        catch: Flow to execute on error (optional)
        finally_: Flow to always execute (optional)

    Returns:
        TryCatch flow

    Example:
        >>> TryCatch(
        ...     child=RiskyOperation(),
        ...     catch=HandleError(),
        ...     finally_=Cleanup(),
        ... )
    """
    return _TryCatch(child=child, catch=catch, finally_=finally_)


def Retry(  # noqa: N802
    child: Flow | Term,
    max_attempts: Term | int = 5,
    delay: Term | float = 1.0,
    backoff: Term | float = 1.5,
    on_retry: Flow | Term | None = None,
) -> _Retry:
    """Retry child on failure with configurable backoff.

    Attempts up to max_attempts times. On failure, waits delay seconds
    (multiplied by backoff each attempt) before retrying.

    Current attempt available via runtime.attributes as "attempt".

    Args:
        child: Flow to retry
        max_attempts: Maximum retry attempts (default: 5)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Delay multiplier after each attempt (default: 1.5)
        on_retry: Optional flow to execute before each retry

    Returns:
        Retry flow

    Example:
        >>> Retry(
        ...     child=NetworkRequest(),
        ...     max_attempts=3,
        ...     delay=1.0,
        ...     backoff=2.0,  # 1s, 2s, 4s delays
        ... )
    """
    return _Retry(
        child=child,
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        on_retry=on_retry,
    )


def Assert(condition: Term | bool, message: str = "Assertion failed") -> _Assert:  # noqa: N802
    """Assert a condition, raising AssertionError if false.

    Args:
        condition: Condition to check (Term or bool)
        message: Error message if assertion fails

    Returns:
        Assert flow

    Example:
        >>> Assert(count.get() > 0, "Count must be positive")
    """
    return _Assert(condition=condition, message=message)
