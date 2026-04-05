"""Functional collection ops — typed factories returning Interface types."""

from .combine import Chain, Enumerate, Zip
from .reduce import All, Any, Max, Min, Sum
from .slice import Drop, Take
from .transform import (
    FilterBy,
    Flatten,
    Pluck,
    Reversed,
    Sorted,
    Unique,
)


__all__ = [
    "All",
    "Any",
    "Chain",
    "Drop",
    "Enumerate",
    "FilterBy",
    "Flatten",
    "Max",
    "Min",
    "Pluck",
    "Reversed",
    "Sorted",
    "Sum",
    "Take",
    "Unique",
    "Zip",
]
