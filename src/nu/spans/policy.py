"""Policy concretes - Retry, TryCatch.

Simple model-aligned shapes. Feature-rich variants (per-attempt
callbacks, exponential backoff, typed exception filters) subclass
and override hooks.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.span import Policy


__all__ = [
    "Retry",
    "TryCatch",
]


class Retry(Policy):
    """`Retry(body, attempts_q)` - re-run body on failure up to N times.

    Simple shape: catch any exception, re-run up to `attempts` times
    total. `attempts` is read from the second child slot if present
    (a Query yielding an int), else defaults to 3.
    """

    body_slot: ClassVar[int] = 0

    def _attempts(self, ctx: Any) -> int:  # noqa: ANN401
        if len(self._children) > 1:
            attempts_node = self._children[1]
            n = attempts_node.eval(ctx)
            return int(n) if n is not None else 3
        return 3

    async def _aattempts(self, ctx: Any) -> int:  # noqa: ANN401
        if len(self._children) > 1:
            attempts_node = self._children[1]
            n = await attempts_node.aeval(ctx)
            return int(n) if n is not None else 3
        return 3

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        n = self._attempts(ctx)
        last_error: BaseException | None = None
        for _ in range(max(1, n)):
            try:
                return call()
            except Exception as e:
                last_error = e
        if last_error is not None:
            raise last_error
        msg = "Retry: attempts <= 0"
        raise RuntimeError(msg)

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        n = await self._aattempts(ctx)
        last_error: BaseException | None = None
        for _ in range(max(1, n)):
            try:
                return await call()
            except Exception as e:
                last_error = e
        if last_error is not None:
            raise last_error
        msg = "Retry: attempts <= 0"
        raise RuntimeError(msg)


class TryCatch(Policy):
    """`TryCatch(body, fallback_body)` - run body; on failure run fallback.

    Simple shape: catches any exception from the body and runs the
    fallback once. Feature-rich variants (typed exception filters,
    exception-bound rebinding) subclass.
    """

    body_slot: ClassVar[int] = 0

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        try:
            return call()
        except Exception:
            if len(self._children) > 1:
                fb = self._children[1]
                fn = getattr(fb, "eval", None) or getattr(fb, "run", None)
                if fn is not None:
                    return fn(ctx)
            raise

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        try:
            return await call()
        except Exception:
            if len(self._children) > 1:
                fb = self._children[1]
                fn = getattr(fb, "aeval", None) or getattr(fb, "arun", None)
                if fn is not None:
                    return await fn(ctx)
            raise
