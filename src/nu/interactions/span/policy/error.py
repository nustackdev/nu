"""Error handling Flow Spans -- TryCatch, Retry (rich).

Subclass the simple new-core ``Span:Policy`` shapes and layer extra
features (typed exception filters, finally branch; per-attempt hooks,
exponential backoff).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from nu.spans.policy import Retry as _CoreRetry
from nu.spans.policy import TryCatch as _CoreTryCatch
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg, IntArg, Nu


__all__ = [
    "Retry",
    "TryCatch",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class TryCatch(_CoreTryCatch):
    """Try/catch/finally with optional typed exception filter.

    Children: ``[body, catch?, finally_?]``. Body at slot 0.
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


class Retry(_CoreRetry):
    """Retry body on failure with exponential backoff and per-attempt hooks.

    Children: ``[body]``. Numeric/hook config kept as instance state so
    Span body-slot semantics stay clean.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

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
