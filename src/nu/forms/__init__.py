"""Native Form nodes.

A form is what a fabric location holds (an Int, a Str, a Dict, a ToList): a
Span over one body that mixes in the surface carrying its methods (``Str`` =
``StrSurface`` on a ``Form[str]``). The surfaces, and the atoms their methods
build, live in ``nu.surfaces``, shared with the refs that hold the same values.
This package holds only the nodes, their constructors, and the atoms only those
constructors build.

Primitive nodes live in ``primitives``, collection nodes (with the dict views
and ``Iterator``) in ``collections``. ``Form``, the kind, lives in ``nu.lang``
and is re-exported here for convenience.
"""

from nu.lang import Form

from .collections import (
    Dict,
    DictItems,
    DictKeys,
    DictValues,
    FrozenSet,
    Iterator,
    List,
    Set,
    Tuple,
)
from .primitives import (
    Bool,
    Bytes,
    Float,
    Int,
    None_,
    NullForm,
    Object,
    Str,
)


__all__ = [
    "Bool",
    "Bytes",
    "Dict",
    "DictItems",
    "DictKeys",
    "DictValues",
    "Float",
    "Form",
    "FrozenSet",
    "Int",
    "Iterator",
    "List",
    "None_",
    "NullForm",
    "Object",
    "Set",
    "Str",
    "Tuple",
]
