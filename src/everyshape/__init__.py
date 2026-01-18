"""EveryShape."""

from __future__ import annotations

from ._exception import EveryShapeError
from .container import Container
from .shape import Shape, Slot
from .term import (
    Command,
    Computation,
    Context,
    LValue,
    Operation,
    RValue,
    Term,
)
from .typing import (
    NOT_SET,
    Empty,
    Invalid,
    NotSet,
    Sentinel,
    Value,
    is_empty,
    is_invalid,
    is_notset,
    is_sentinel,
)
from .view import View


__all__ = [
    "NOT_SET",
    "Command",
    "Computation",
    "Container",
    "Context",
    "Empty",
    "EveryShapeError",
    "Invalid",
    "LValue",
    "NotSet",
    "Operation",
    "RValue",
    "Sentinel",
    "Shape",
    "Slot",
    "Term",
    "Term",
    "Value",
    "View",
    "is_empty",
    "is_invalid",
    "is_notset",
    "is_sentinel",
]
