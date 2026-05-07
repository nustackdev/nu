"""virtuals-specific spans.

Atomic boundaries (Atomic / Snapshot / Transaction) and conflict-aware
retry preset (RetryOnConflict).
"""

from .atomic import Atomic, Snapshot, Transaction
from .retry_on_conflict import CONFLICT_ERRORS, RetryOnConflict


__all__ = [
    "CONFLICT_ERRORS",
    "Atomic",
    "RetryOnConflict",
    "Snapshot",
    "Transaction",
]
