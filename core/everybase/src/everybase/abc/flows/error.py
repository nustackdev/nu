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
    provided, the handler runs with ctx extended with ``"error"`` tag
    containing ``str(exception)``. If no *catch* is provided the exception
    propagates after the *finally_* block (if any) completes.

    Example::

        TryCatch(
            risky_operation,
            catch=error_handler,
            finally_=cleanup,
        )
    """

    def __init__(
        self,
        body: Executable,
        catch: Executable | None = None,
        finally_: Executable | None = None,
    ) -> None:
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
                catch_ctx = ctx.bind(str(e), "error")
                await self.children[catch_idx].execute(catch_ctx)
        finally:
            if finally_idx is not None:
                await self.children[finally_idx].execute(ctx)

        if caught is not None and not self._has_catch:
            raise caught


class Retry(Flow):
    """Retry child on failure with exponential backoff.

    Children layout: ``[body, max_attempts, delay, backoff,
                        on_attempt_fail?, on_success?, on_fail?]``

    Executes *body* up to *max_attempts* times.

    Hooks receive ctx extended with ``"error"`` (str) and ``"attempt"`` (int) tags:
    - ``on_attempt_fail``: fires on every non-final failure (before sleep + retry)
    - ``on_success``: fires after successful execution
    - ``on_fail``: fires on final failure (before re-raise)

    Example::

        Retry(
            fetch_data,
            max_attempts=5,
            delay=1.0,
            backoff=2.0,
            on_attempt_fail=log_retry,
            on_fail=alert_failure,
        )
    """

    def __init__(
        self,
        body: Executable,
        *,
        max_attempts: IntArg = 3,
        delay: FloatArg = 0.0,
        backoff: FloatArg = 1.0,
        on_attempt_fail: Executable | None = None,
        on_success: Executable | None = None,
        on_fail: Executable | None = None,
    ) -> None:
        children: list[Executable] = [
            body,
            ensure_term(max_attempts),
            ensure_term(delay),
            ensure_term(backoff),
        ]
        self._has_on_attempt_fail = on_attempt_fail is not None
        self._has_on_success = on_success is not None
        self._has_on_fail = on_fail is not None

        if on_attempt_fail is not None:
            children.append(on_attempt_fail)
        if on_success is not None:
            children.append(on_success)
        if on_fail is not None:
            children.append(on_fail)

        super().__init__(*children)

    @property
    def has_hooks(self) -> bool:
        """True if any hook is set."""
        return self._has_on_attempt_fail or self._has_on_success or self._has_on_fail

    def _hook_indices(self) -> tuple[int | None, int | None, int | None]:
        """Return (on_attempt_fail_idx, on_success_idx, on_fail_idx)."""
        idx = 4
        af_idx = None
        s_idx = None
        f_idx = None
        if self._has_on_attempt_fail:
            af_idx = idx
            idx += 1
        if self._has_on_success:
            s_idx = idx
            idx += 1
        if self._has_on_fail:
            f_idx = idx
        return af_idx, s_idx, f_idx

    async def execute(self, ctx: Context) -> None:
        """Execute body with retry logic and exponential backoff."""
        body = self.children[0]
        max_attempts = await self.children[1].execute(ctx)
        delay = await self.children[2].execute(ctx)
        backoff = await self.children[3].execute(ctx)
        af_idx, s_idx, f_idx = self._hook_indices()

        for attempt in range(1, max_attempts + 1):
            try:
                await body.execute(ctx)
                if s_idx is not None:
                    hook_ctx = ctx.bind(attempt, "attempt")
                    await self.children[s_idx].execute(hook_ctx)
                return
            except Exception as e:
                hook_ctx = ctx.bind(str(e), "error").bind(attempt, "attempt")
                if attempt >= max_attempts:
                    if f_idx is not None:
                        await self.children[f_idx].execute(hook_ctx)
                    raise
                if af_idx is not None:
                    await self.children[af_idx].execute(hook_ctx)
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
        super().__init__(ensure_term(condition))
        self._message = message

    async def execute(self, ctx: Context) -> None:
        """Evaluate condition and raise AssertionError if falsy."""
        result = await self.children[0].execute(ctx)
        if not result:
            raise AssertionError(self._message)
