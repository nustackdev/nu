"""EveryShape."""

from __future__ import annotations

from ._exception import EveryShapeError
from ._types import NOT_SET, NotSet, is_notset
from .container import Container
from .shape import Shape, Slot
from .term import Command, Context, Operation, Term
from .types import Empty, NaN, SpecialValue, Value, is_empty, is_nan, is_special
from .view import View


__all__ = [
    "NOT_SET",
    "Command",
    "Container",
    "Context",
    "Empty",
    "EveryShapeError",
    "NaN",
    "NotSet",
    "Operation",
    "Shape",
    "Slot",
    "SpecialValue",
    "Term",
    "Value",
    "View",
    "is_empty",
    "is_nan",
    "is_notset",
    "is_special",
]
