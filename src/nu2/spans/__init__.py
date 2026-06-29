"""Span atoms: transparent Interactions that wrap a body to govern a region.

A Span does no work of its own; it forwards the body's yield in the same shape
(TRANSPARENT cardinality) and shapes the surroundings - lifecycle (Bracket) or
execution policy (Policy). The body is the required slot-0 child; auxiliary
children sit alongside and are consumed internally.

Ported from v1 ``src/nu/spans/`` (``bracket`` / ``policy`` / ``timing``). So
far: Policy ``TryCatch``. Bracket (Snapshot, Transaction) is fabric-specific and
lands with the fabric work; the remaining Policy/timing spans (Retry, Timeout,
Throttle, Debounce) follow.
"""

from __future__ import annotations

from .policy import TryCatch


__all__ = ["TryCatch"]
