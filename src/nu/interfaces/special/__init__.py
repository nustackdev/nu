"""Special interfaces."""

from .any_ import AnyI
from .iterator_ import IteratorI
from .sentinel_ import EmptyI, InvalidI, SentinelI


__all__ = [
    "AnyI",
    "EmptyI",
    "InvalidI",
    "IteratorI",
    "SentinelI",
]
