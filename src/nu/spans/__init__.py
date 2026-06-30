"""Span atoms: transparent Interactions that wrap a body to govern a region.

A Span does no work of its own; it forwards the body's yield in the same shape
(TRANSPARENT cardinality) and shapes the surroundings - lifecycle (Bracket) or
execution policy (Policy). The body is the required slot-0 child; auxiliary
children sit alongside and are consumed internally.

Policy:
``TryCatch``, ``Retry``, ``Timeout``, ``Throttle``, ``Debounce`` - execution
policy on failure or in time.

Bracket:
``Snapshot``, ``Transaction`` - lifecycle boundaries. The core ships them as
model-level shapes with no-op hooks (a bare bracket runs its body); a fabric
subclasses them and overrides the lifecycle hooks to drive a real store.
"""

from __future__ import annotations

from .bracket import Snapshot, Transaction
from .policy import Debounce, Retry, Throttle, Timeout, TryCatch


__all__ = ["Debounce", "Retry", "Snapshot", "Throttle", "Timeout", "Transaction", "TryCatch"]
