"""RetryOnConflict — virtuals-specific Retry preset.

Wraps `nu.Retry` with the virtuals storage conflict-error tuple
(`StorageTransactionConflictError`, `StorageLockTimeoutError`) and
sensible defaults: 5 attempts, 100ms base delay, 2x backoff, 50% jitter.

Pattern::

    RetryOnConflict(Transaction(body))

Decorrelates retries across concurrent writers so they don't re-collide
in lockstep on the same hot keys (e.g. shared `__len__` metadata).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.spans.policy import Retry
from virtuals.tkv.storage import (
    StorageLockTimeoutError,
    StorageTransactionConflictError,
)


if TYPE_CHECKING:
    from nu import Nu
    from nu.terms import FloatArg, IntArg


__all__ = [
    "CONFLICT_ERRORS",
    "RetryOnConflict",
]


CONFLICT_ERRORS: tuple[type[Exception], ...] = (
    StorageTransactionConflictError,
    StorageLockTimeoutError,
)


class RetryOnConflict(Retry):
    """Retry preset for virtuals storage conflicts.

    Targets `StorageTransactionConflictError` and `StorageLockTimeoutError`
    only — non-conflict exceptions propagate immediately. Defaults are
    tuned for hot-key contention under N concurrent writers.

    Override any kwarg to tune. `errors` is fixed to the conflict tuple
    by default; pass `errors=...` to extend or replace the filter.
    """

    body_slot: ClassVar[int] = 0

    def __init__(
        self,
        body: Nu,
        *,
        max_attempts: IntArg = 5,
        delay: FloatArg = 0.1,
        backoff: FloatArg = 2.0,
        jitter: FloatArg = 0.5,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
        on_attempt_fail: Nu | None = None,
        on_success: Nu | None = None,
        on_fail: Nu | None = None,
    ) -> None:
        super().__init__(
            body,
            max_attempts=max_attempts,
            delay=delay,
            backoff=backoff,
            jitter=jitter,
            errors=CONFLICT_ERRORS if errors is None else errors,
            on_attempt_fail=on_attempt_fail,
            on_success=on_success,
            on_fail=on_fail,
        )
