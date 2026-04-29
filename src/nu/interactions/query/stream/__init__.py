"""Stream queries - multi-value functional construction."""

from .fold import Fold
from .iter import Iter
from .transform import Filter, Map, TakeWhile, UniqueDo


__all__ = [
    "Filter",
    "Fold",
    "Iter",
    "Map",
    "TakeWhile",
    "UniqueDo",
]
