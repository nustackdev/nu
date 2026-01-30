"""Abstract ref bases combining traits.

These are abstract bases that combine traits for common value types.
Concrete implementations (like IntRef in py/) inherit from these
and add substrate-specific get() implementations.

Example:
    IntRefBase = Numeric + Comparable + Logical + Bitwise + base execution
    IntRef(IntRefBase) = IntRefBase + Python memory get()
    KVIntRef(IntRefBase) = IntRefBase + KV storage get()
"""

from ._base import RefBase
from .any import AnyRefBase
from .bool import BoolRefBase
from .bytes import BytesRefBase
from .dict import DictRefBase
from .float import FloatRefBase
from .int import IntRefBase
from .list import ListRefBase
from .none import NoneRefBase
from .sentinel import EmptyRefBase, InvalidRefBase, SentinelRefBase
from .set import FrozenSetRefBase, SetRefBase
from .str import StrRefBase
from .tuple import TupleRefBase


__all__ = [  # noqa: RUF022
    "RefBase",
    # Primitives
    "BoolRefBase",
    "IntRefBase",
    "FloatRefBase",
    "StrRefBase",
    "BytesRefBase",
    # Collections
    "ListRefBase",
    "DictRefBase",
    "SetRefBase",
    "FrozenSetRefBase",
    "TupleRefBase",
    # Special
    "AnyRefBase",
    "NoneRefBase",
    "SentinelRefBase",
    "EmptyRefBase",
    "InvalidRefBase",
]
