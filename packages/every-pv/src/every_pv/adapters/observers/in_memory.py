"""In-memory observer implementation with thread-safe subscription management.

The InMemoryObserver provides efficient pattern matching using the
SubscriptionRegistry from the base class. All subscription logic is
handled by BaseObserver - this class only provides connection management.
"""

from __future__ import annotations


try:
    from tkv.observers.mem import InMemoryObserver
except ImportError as e:
    raise ImportError(
        "tkv package is required for InMemoryObserver. Install via: pip install tkv"
    ) from e


__all__ = [
    "InMemoryObserver",
]
