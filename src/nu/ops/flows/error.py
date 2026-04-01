"""Error handling flows -- TryCatch, Retry, Assert."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from .base import Flow

from nu.utils import ensure_nu
from nu.interfaces.values import NoneValue


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu, FloatArg, IntArg


__all__ = [
    "Assert",
    "Retry",
    "TryCatch",
]


class TryCatch(Flow):
    """Try/catch/finally error handling.

    Children layout: ``[body, catch, finally_]``

    Always 3 children. Missing handlers are ``NoneValue()`` sentinels.

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
        body: Nu,
        catch: Nu | None = None,
        finally_: Nu | None = None,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
    ) -> None:
        _none = NoneValue()
        super().__init__(body, catch or _none, finally_ or _none)
        if errors is not None and not isinstance(errors, tuple):
            errors = (errors,)
        self._errors = errors

    @property
    def catch(self) -> Nu | None:
        """Catch handler, or None if absent."""
        c = self.children[1]
        return None if isinstance(c, NoneValue) else c

    @property
    def finally_(self) -> Nu | None:
        """Finally handler, or None if absent."""
        c = self.children[2]
        return None if isinstance(c, NoneValue) else c

    async def execute(self, ctx: Context) -> None:
        """Execute with try/catch/finally semantics.

        If ``errors`` is set, only matching exception types are caught.
        Non-matching exceptions propagate (after finally).
        """
        body = self.children[0]
        catch = self.catch
        finally_ = self.finally_

        caught: Exception | None = None
        handled = False
        try:
            await body.execute(ctx)
        except Exception as e:
            caught = e
            if catch is not None and (self._errors is None or isinstance(e, self._errors)):
                catch_ctx = ctx._copy()
                catch_ctx.attrs["error"] = str(e)
                await catch.execute(catch_ctx)
                handled = True
        finally:
            if finally_ is not None:
                await finally_.execute(ctx)

        if caught is not None and not handled:
            raise caught


class Retry(Flow):
    """Retry child on failure with exponential backoff.

    Children layout: ``[body, max_attempts, delay, backoff,
                        on_attempt_fail, on_success, on_fail]``

    Always 7 children. Missing hooks are ``NoneValue()`` sentinels.

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
        body: Nu,
        *,
        max_attempts: IntArg = 3,
        delay: FloatArg = 0.0,
        backoff: FloatArg = 1.0,
        on_attempt_fail: Nu | None = None,
        on_success: Nu | None = None,
        on_fail: Nu | None = None,
    ) -> None:
        _none = NoneValue()
        super().__init__(
            body,
            ensure_nu(max_attempts),
            ensure_nu(delay),
            ensure_nu(backoff),
            on_attempt_fail or _none,
            on_success or _none,
            on_fail or _none,
        )

    @property
    def on_attempt_fail(self) -> Nu | None:
        """On-attempt-fail hook, or None if absent."""
        c = self.children[4]
        return None if isinstance(c, NoneValue) else c

    @property
    def on_success(self) -> Nu | None:
        """On-success hook, or None if absent."""
        c = self.children[5]
        return None if isinstance(c, NoneValue) else c

    @property
    def on_fail(self) -> Nu | None:
        """On-fail hook, or None if absent."""
        c = self.children[6]
        return None if isinstance(c, NoneValue) else c

    @property
    def has_hooks(self) -> bool:
        """True if any hook is set."""
        return (
            self.on_attempt_fail is not None
            or self.on_success is not None
            or self.on_fail is not None
        )

    async def execute(self, ctx: Context) -> None:
        """Execute body with retry logic and exponential backoff."""
        body = self.children[0]
        max_attempts = await self.children[1].execute(ctx)
        delay = await self.children[2].execute(ctx)
        backoff = await self.children[3].execute(ctx)

        for attempt in range(1, max_attempts + 1):
            try:
                await body.execute(ctx)
                hook = self.on_success
                if hook is not None:
                    hook_ctx = ctx._copy()
                    hook_ctx.attrs["attempt"] = attempt
                    await hook.execute(hook_ctx)
                return
            except Exception as e:
                hook_ctx = ctx._copy()
                hook_ctx.attrs["error"] = str(e)
                hook_ctx.attrs["attempt"] = attempt
                if attempt >= max_attempts:
                    hook = self.on_fail
                    if hook is not None:
                        await hook.execute(hook_ctx)
                    raise
                hook = self.on_attempt_fail
                if hook is not None:
                    await hook.execute(hook_ctx)
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
        super().__init__(ensure_nu(condition))
        self._message = message

    async def execute(self, ctx: Context) -> None:
        """Evaluate condition and raise AssertionError if falsy."""
        result = await self.children[0].execute(ctx)
        if not result:
            raise AssertionError(self._message)
