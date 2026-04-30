"""Policy concretes - Retry, TryCatch.

Both have full sync + async surface. Retry supports max_attempts, delay,
backoff, and per-attempt hooks (async only); TryCatch supports a typed
exception filter and a `finally` branch.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.span import Policy
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg, IntArg, Nu


__all__ = [
    "Retry",
    "TryCatch",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class TryCatch(Policy):
    """Try/catch/finally with optional typed exception filter.

    Children: ``[body, catch?]``. Body at slot 0. ``finally_`` runs on
    success or failure.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        body: Nu,
        catch: Nu | None = None,
        finally_: Nu | None = None,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
    ) -> None:
        children: list = [body]
        if catch is not None:
            children.append(catch)
        super().__init__(*children)
        self._finally = finally_
        if errors is not None and not isinstance(errors, tuple):
            errors = (errors,)
        self._errors: tuple[type[Exception], ...] | None = errors

    @property
    def catch(self) -> Nu | None:
        return self._children[1] if len(self._children) > 1 else None

    @property
    def finally_(self) -> Nu | None:
        return self._finally

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        from nu import runtime

        try:
            try:
                return call()
            except Exception as e:
                if self._errors is not None and not isinstance(e, self._errors):
                    raise
                fb = self.catch
                if fb is None:
                    raise
                catch_ctx = ctx._copy() if hasattr(ctx, "_copy") else ctx
                if hasattr(catch_ctx, "attrs"):
                    catch_ctx.attrs["error"] = str(e)
                return runtime.execute(fb, catch_ctx)
        finally:
            if self._finally is not None:
                runtime.execute(self._finally, ctx)

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        from nu import runtime

        try:
            try:
                return await call()
            except Exception as e:
                if self._errors is not None and not isinstance(e, self._errors):
                    raise
                fb = self.catch
                if fb is None:
                    raise
                catch_ctx = ctx._copy() if hasattr(ctx, "_copy") else ctx
                if hasattr(catch_ctx, "attrs"):
                    catch_ctx.attrs["error"] = str(e)
                return await runtime.aexecute(fb, catch_ctx)
        finally:
            if self._finally is not None:
                await runtime.aexecute(self._finally, ctx)


class Retry(Policy):
    """Retry body on failure with exponential backoff and per-attempt hooks.

    Children: ``[body]``. Numeric/hook config kept as instance state so
    Span body-slot semantics stay clean. Sync mode runs basic retry
    (no delay or hooks); async mode supports `delay`, `backoff`, and
    `on_attempt_fail` / `on_success` / `on_fail` hooks.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = _BOTH

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
        super().__init__(body)
        self._max_attempts = max_attempts
        self._delay = delay
        self._backoff = backoff
        self._on_attempt_fail = on_attempt_fail
        self._on_success = on_success
        self._on_fail = on_fail

    @property
    def on_attempt_fail(self) -> Nu | None:
        return self._on_attempt_fail

    @property
    def on_success(self) -> Nu | None:
        return self._on_success

    @property
    def on_fail(self) -> Nu | None:
        return self._on_fail

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        max_attempts = self._max_attempts if isinstance(self._max_attempts, int) else 3
        last_error: BaseException | None = None
        for _ in range(max(1, max_attempts)):
            try:
                return call()
            except Exception as e:
                last_error = e
        if last_error is not None:
            raise last_error
        msg = "Retry: attempts <= 0"
        raise RuntimeError(msg)

    async def _resolve(self, ctx: Any, val: Any) -> Any:  # noqa: ANN401
        from nu import runtime
        from nu.terms.nu import NuBase

        if isinstance(val, NuBase):
            return await runtime.afirst(val, ctx)
        return val

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        from nu import runtime

        max_attempts = int(await self._resolve(ctx, self._max_attempts))
        delay = float(await self._resolve(ctx, self._delay))
        backoff = float(await self._resolve(ctx, self._backoff))

        for attempt in range(1, max_attempts + 1):
            try:
                result = await call()
                if self._on_success is not None:
                    hook_ctx = ctx._copy() if hasattr(ctx, "_copy") else ctx
                    if hasattr(hook_ctx, "attrs"):
                        hook_ctx.attrs["attempt"] = attempt
                    await runtime.aexecute(self._on_success, hook_ctx)
                return result
            except Exception as e:
                hook_ctx = ctx._copy() if hasattr(ctx, "_copy") else ctx
                if hasattr(hook_ctx, "attrs"):
                    hook_ctx.attrs["error"] = str(e)
                    hook_ctx.attrs["attempt"] = attempt
                if attempt >= max_attempts:
                    if self._on_fail is not None:
                        await runtime.aexecute(self._on_fail, hook_ctx)
                        return None
                    raise
                if self._on_attempt_fail is not None:
                    await runtime.aexecute(self._on_attempt_fail, hook_ctx)
                await asyncio.sleep(delay)
                delay *= backoff
        return None
