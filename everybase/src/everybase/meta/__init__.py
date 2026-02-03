"""everybase.meta — Tree meta-programming.

Structural rewrites that inject cross-cutting concerns
(transactions, logging, tracing, …) into expression trees.
"""

from .transforms import conditional_wrap


__all__ = [
    "conditional_wrap",
]
