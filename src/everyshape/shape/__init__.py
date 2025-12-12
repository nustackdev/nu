"""Layer 4 - declarative access."""

from .context import ContextProtocol
from .core.binary_ops import BinaryOp
from .core.literal_value import LiteralValue, literal
from .core.unary_ops import UnaryOp
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


__all__ = [
    "BinaryOp",
    "Command",
    "ContextProtocol",
    "LValue",
    "LiteralValue",
    "Operation",
    "PrimitiveRef",
    "RValue",
    "Ref",
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
    "Term",
    "UnaryOp",
    "ViewRef",
    "literal",
]
