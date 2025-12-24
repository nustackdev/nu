"""Layer 4 - declarative access."""

from .combiners import all_, and_, any_, none_, or_
from .context import ContextProtocol
from .shape import (
    Shape,
    ShapeMeta,
    Slot,
    SlotDescriptor,
)
from .term import (
    Command,
    LValue,
    Operation,
    PrimitiveRef,
    Ref,
    RValue,
    Term,
    ViewRef,
)


# from .refs import
# from .literals import


__all__ = [
    "Command",
    "ContextProtocol",
    "LValue",
    "Operation",
    "PrimitiveRef",
    "RValue",
    "Ref",
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
    "Term",
    "ViewRef",
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
]
