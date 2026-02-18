"""Error handling flows -- TryCatch, Retry, Assert."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from everybase import Flow

from ..utils import ensure_term


if TYPE_CHECKING:
    from everybase import Context, Executable, FloatArg, IntArg


__all__ = [
    "Assert",
    "Retry",
    "TryCatch",
]


class TryCatch(Flow):
    """Try/catch/finally error handling.

    Children layout: ``[body, catch?, finally?]``

    Executes *body*. If an exception occurs and a *catch* handler is
    provided, the handler runs (and the optional *error* Ref is written
    with ``str(exception)``). If no *catch* is provided the exception
    propagates after the *finally_* block (if any) completes.

    Example::

        err = Var("")
        TryCatch(
            risky_operation,
            catch=error_handler,
            finally_=cleanup,
            error=err,
        )
    """

    def __init__(
        self,
        body: Executable,
        catch: Executable | None = None,
        finally_: Executable | None = None,
    ) -> None:
        """Initialize try/catch/finally flow.

        Args:
            body: Main execution body.
            catch: Executed on exception (optional).
            finally_: Executed always after body/catch (optional).
        """
        children: list[Executable] = [body]

        self._has_catch = catch is not None
        self._has_finally = finally_ is not None

        if catch is not None:
            children.append(catch)
        if finally_ is not None:
            children.append(finally_)

        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute with try/catch/finally semantics."""
        body = self.children[0]
        catch_idx = 1 if self._has_catch else None
        finally_idx: int | None = None
        if self._has_finally:
            finally_idx = 2 if self._has_catch else 1

        caught: Exception | None = None
        try:
            await body.execute(ctx)
        except Exception as e:
            caught = e
            if catch_idx is not None:
                await self.children[catch_idx].execute(ctx)
        finally:
            if finally_idx is not None:
                await self.children[finally_idx].execute(ctx)

        if caught is not None and not self._has_catch:
            raise caught


class Retry(Flow):
    """Retry child on failure with exponential backoff.

    Children layout: ``[body, max_attempts, delay, backoff, on_retry?]``

    Executes *body* up to *max_attempts* times. On each failure the
    optional *on_retry* handler runs, then the flow sleeps for *delay*
    seconds before the next attempt. After each retry *delay* is
    multiplied by *backoff* for exponential back-off.

    Example::

        attempt = Var(0)
        Retry(
            fetch_data,
            max_attempts=5,
            delay=1.0,
            backoff=2.0,
            on_retry=log_retry,
            attempt=attempt,
        )
    """

    def __init__(
        self,
        body: Executable,
        *,
        max_attempts: IntArg = 3,
        delay: FloatArg = 0.0,
        backoff: FloatArg = 1.0,
        on_retry: Executable | None = None,
    ) -> None:
        """Initialize retry flow.

        Args:
            body: Execution body to retry on failure.
            max_attempts: Maximum number of attempts (int or Term).
            delay: Initial delay in seconds between retries (float or Term).
            backoff: Multiplier applied to delay after each retry (float or Term).
            on_retry: Executed after each failed attempt before sleeping (optional).

        """
        children: list[Executable] = [
            body,
            ensure_term(max_attempts),
            ensure_term(delay),
            ensure_term(backoff),
        ]
        self._has_on_retry = on_retry is not None
        if on_retry is not None:
            children.append(on_retry)
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Execute body with retry logic and exponential backoff."""
        body = self.children[0]
        max_attempts = await self.children[1].execute(ctx)
        delay = await self.children[2].execute(ctx)
        backoff = await self.children[3].execute(ctx)

        for attempt in range(1, max_attempts + 1):
            try:
                await body.execute(ctx)
                return
            except Exception:
                if attempt >= max_attempts:
                    raise
                if self._has_on_retry:
                    await self.children[4].execute(ctx)
                await asyncio.sleep(delay)
                delay *= backoff


class Assert(Flow):
    """Validate a condition during execution.

    Children layout: ``[condition]``

    Evaluates *condition* and raises ``AssertionError`` with the given
    *message* when the result is falsy.

    Example::

        Assert(count > 0, message="count must be positive")
        Assert(user_exists, message="user not found")
    """

    def __init__(self, condition: Any, message: str = "Assertion failed") -> None:
        """Initialize assertion flow.

        Args:
            condition: Term or literal evaluated as boolean.
            message: Error message raised when condition is falsy.
        """
        super().__init__(ensure_term(condition))
        self._message = message

    async def execute(self, ctx: Context) -> None:
        """Evaluate condition and raise AssertionError if falsy."""
        result = await self.children[0].execute(ctx)
        if not result:
            raise AssertionError(self._message)
