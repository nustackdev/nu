"""Example: Retry with hooks and annotate_retries deformation."""

from __future__ import annotations

import asyncio
import logging

from nu import Context, annotate_retries
from nu.abc import Print, Retry
from nu.abc.refs import IntRef, StrRef


logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


# --- A flaky operation that fails a few times then succeeds ---


class FlakyFetch:
    """Simulates an unreliable network call."""

    is_leaf = True
    children = ()

    def __init__(self, fail_times: int = 2) -> None:
        self._fail_times = fail_times
        self._calls = 0

    @property
    def is_self_pure(self) -> bool:
        return True

    def with_children(self, *c: object) -> FlakyFetch:
        return self

    async def execute(self, ctx: Context) -> str:
        self._calls += 1
        if self._calls <= self._fail_times:
            msg = f"connection refused (call #{self._calls})"
            raise ConnectionError(msg)
        return "data loaded"


async def main() -> None:
    # ── 1. Retry with explicit hooks ──
    # Hooks use primitive refs to read "error" and "attempt" from ctx
    error = StrRef("error")
    attempt = IntRef("attempt")

    retry_with_hooks = Retry(
        FlakyFetch(fail_times=2),
        max_attempts=5,
        delay=0.05,
        backoff=2.0,
        on_attempt_fail=Print("RETRY", error.get(), attempt.get()),
        on_success=Print("OK after attempts:", attempt.get()),
    )

    print("=== Retry with explicit hooks ===")
    await retry_with_hooks.execute(Context())

    # ── 2. Bare Retry + annotate_retries deformation ──
    # No hooks — annotate_retries auto-adds Log-based hooks
    bare_retry = Retry(FlakyFetch(fail_times=2), max_attempts=4, delay=0.05)
    print(f"\nbefore annotate_retries: has_hooks = {bare_retry.has_hooks}")

    annotated = annotate_retries(bare_retry)
    print(f"after  annotate_retries: has_hooks = {annotated.has_hooks}")

    print("\n=== Running annotated retry (watch WARNING logs) ===")
    await annotated.execute(Context())

    print("\ndone")


if __name__ == "__main__":
    asyncio.run(main())
