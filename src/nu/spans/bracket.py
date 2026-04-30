"""Bracket concretes - Snapshot, Transaction.

Lightweight model-aligned shapes. Concrete fabric-aware variants
subclass and override the lifecycle hooks.
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms.span import Bracket


__all__ = [
    "Snapshot",
    "Transaction",
]


class Snapshot(Bracket):
    """Snapshot the body's reads. No commit on success.

    Lightweight Bracket - hooks are no-ops at the term level; concrete
    fabric-aware Snapshots subclass and override.
    """

    body_slot: ClassVar[int] = 0


class Transaction(Bracket):
    """Atomic body execution: commit on success, rollback on failure.

    Simple shape: `before` opens a transaction, `after` commits,
    `after_failure` rolls back. Concrete fabric-aware Transactions
    subclass and override these to talk to the actual store.
    """

    body_slot: ClassVar[int] = 0
