"""Error handling ops -- TryCatch, Retry, Assert."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from nu.interfaces import NoneI
from nu.terms.op import Calculation, Command


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import FloatArg, IntArg, Nu, StrArg


__all__ = [
    "Assert",
    "Retry",
    "TryCatch",
]


class TryCatch(Calculation):
    """Try/catch/finally error handling.

    Children: ``[body, catch, finally_]``

    Always 3 children. Missing handlers are ``NoneI()`` sentinels.
    """

    def __init__(
        self,
        body: Nu,
        catch: Nu | None = None,
        finally_: Nu | None = None,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
    ) -> None:
        _none = NoneI()
        super().__init__(body, catch or _none, finally_ or _none)
        if errors is not None and not isinstance(errors, tuple):
            errors = (errors,)
        self._errors = errors

    @property
    def catch(self) -> Nu | None:
        c = self.children[1]
        return None if isinstance(c, NoneI) else c

    @property
    def finally_(self) -> Nu | None:
        c = self.children[2]
        return None if isinstance(c, NoneI) else c

    async def execute(self, ctx: Context) -> None:
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


class Retry(Command):
    """Retry child on failure with exponential backoff.

    Children: ``[body, max_attempts, delay, backoff,
                on_attempt_fail, on_success, on_fail]``

    Always 7 children. Missing hooks are ``NoneI()`` sentinels.
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
        _none = NoneI()
        super().__init__(
            body, max_attempts, delay, backoff,
            on_attempt_fail or _none,
            on_success or _none,
            on_fail or _none,
        )

    @property
    def on_attempt_fail(self) -> Nu | None:
        c = self.children[4]
        return None if isinstance(c, NoneI) else c

    @property
    def on_success(self) -> Nu | None:
        c = self.children[5]
        return None if isinstance(c, NoneI) else c

    @property
    def on_fail(self) -> Nu | None:
        c = self.children[6]
        return None if isinstance(c, NoneI) else c

    async def execute(self, ctx: Context) -> None:
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


class Assert(Command):
    """Validate a condition during execution.

    Children: ``[condition, message]``

    Raises ``AssertionError`` when condition is falsy.
    """

    def __init__(self, condition: Any, message: StrArg = "Assertion failed") -> None:
        super().__init__(condition, message)

    async def execute(self, ctx: Context) -> None:
        result = await self.children[0].execute(ctx)
        if not result:
            message = await self.children[1].execute(ctx)
            raise AssertionError(message)
