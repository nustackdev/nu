"""Span interactions - concrete Bracket and Policy kinds.

Generic Spans (Snapshot, Transaction, Retry, TryCatch) live in
`nu.terms.span`. This package adds domain-specific subclasses.
"""

from .policy import Debounce, Retry, Throttle, Timeout, TryCatch


__all__ = [
    "Debounce",
    "Retry",
    "Throttle",
    "Timeout",
    "TryCatch",
]
