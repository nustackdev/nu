"""Error handling Flow Commands -- TryCatch, Retry."""

from __future__ import annotations

import asyncio
from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.primitives import NoneI
from nu.terms import Flow, Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import FloatArg, IntArg, Nu


__all__ = [
    "Retry",
    "TryCatch",
]


class TryCatch(Flow):
    """Try/catch/finally error handling.

    Children: ``[body, catch, finally_]``

    Always 3 children. Missing handlers are ``NoneI()`` sentinels.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

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

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        body = self.children[0]
        catch = self.catch
        finally_ = self.finally_

        caught: Exception | None = None
        handled = False
        try:
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v
        except Exception as e:
            caught = e
            if catch is not None and (self._errors is None or isinstance(e, self._errors)):
                catch_ctx = ctx._copy()
                catch_ctx.attrs["error"] = str(e)
                async with aclosing(catch.aopen(catch_ctx)) as gen:
                    async for v in gen:
                        yield v
                handled = True
        finally:
            if finally_ is not None:
                async with aclosing(finally_.aopen(ctx)) as gen:
                    async for v in gen:
                        yield v

        if caught is not None and not handled:
            raise caught

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        body = self.children[0]
        catch = self.catch
        finally_ = self.finally_

        caught: Exception | None = None
        handled = False
        try:
            with closing(body.open(ctx)) as gen:
                yield from gen
        except Exception as e:
            caught = e
            if catch is not None and (self._errors is None or isinstance(e, self._errors)):
                catch_ctx = ctx._copy()
                catch_ctx.attrs["error"] = str(e)
                with closing(catch.open(catch_ctx)) as gen:
                    yield from gen
                handled = True
        finally:
            if finally_ is not None:
                with closing(finally_.open(ctx)) as gen:
                    yield from gen

        if caught is not None and not handled:
            raise caught


class Retry(Flow):
    """Retry child on failure with exponential backoff.

    Children: ``[body, max_attempts, delay, backoff,
                on_attempt_fail, on_success, on_fail]``

    Always 7 children. Missing hooks are ``NoneI()`` sentinels.
    """

    own_mode: ClassVar[Mode] = Mode.ASYNC
    func_mode: ClassVar[Mode] = Mode.ASYNC

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
            body,
            max_attempts,
            delay,
            backoff,
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

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        body = self.children[0]
        max_attempts = await self.children[1].afirst(ctx)
        delay = await self.children[2].afirst(ctx)
        backoff = await self.children[3].afirst(ctx)

        for attempt in range(1, max_attempts + 1):
            try:
                async with aclosing(body.aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
                hook = self.on_success
                if hook is not None:
                    hook_ctx = ctx._copy()
                    hook_ctx.attrs["attempt"] = attempt
                    await hook.aexecute(hook_ctx)
                return
            except Exception as e:
                hook_ctx = ctx._copy()
                hook_ctx.attrs["error"] = str(e)
                hook_ctx.attrs["attempt"] = attempt
                if attempt >= max_attempts:
                    hook = self.on_fail
                    if hook is not None:
                        await hook.aexecute(hook_ctx)
                    else:
                        raise
                hook = self.on_attempt_fail
                if hook is not None:
                    await hook.aexecute(hook_ctx)
                await asyncio.sleep(delay)
                delay *= backoff
