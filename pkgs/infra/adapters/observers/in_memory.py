"""In-memory observer implementation with thread-safe subscription management.

The InMemoryObserver provides efficient pattern matching using the
SubscriptionRegistry from the base class. All subscription logic is
handled by BaseObserver - this class only provides connection management.
"""

from __future__ import annotations


try:
    from evkv.observers.in_memory import InMemoryObserver
except ImportError as e:
    raise ImportError(
        "evkv package is required for InMemoryObserver. Install via: pip install evkv"
    ) from e


__all__ = [
    "InMemoryObserver",
]
