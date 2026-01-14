"""EveryShape."""

from __future__ import annotations

from ._exception import EveryShapeError
from .container import Container
from .shape import Shape, Slot
from .term import (
    Command,
    Computation,
    ComputedValue,
    Context,
    LiteralValue,
    LValue,
    Operation,
    RValue,
    Term,
    ValueTerm,
)
from .typing import (
    NOT_SET,
    Empty,
    NaN,
    NotSet,
    Sentinel,
    Value,
    is_empty,
    is_nan,
    is_notset,
    is_special,
)
from .view import View


__all__ = [
    "NOT_SET",
    "Command",
    "Computation",
    "ComputedValue",
    "Container",
    "Context",
    "Empty",
    "EveryShapeError",
    "LValue",
    "LiteralValue",
    "NaN",
    "NotSet",
    "Operation",
    "RValue",
    "Sentinel",
    "Shape",
    "Slot",
    "Term",
    "Value",
    "ValueTerm",
    "View",
    "is_empty",
    "is_nan",
    "is_notset",
    "is_special",
]
