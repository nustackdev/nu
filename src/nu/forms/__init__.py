"""Native Form layer.

A form is what a fabric location holds (an Int, a Str, a Dict, a ToList) and the
fluent typed surface for building Nu over it. Each family is two classes: a
``Surface`` that carries the methods (``StrSurface``) and the ``Form`` node, a
Span over one body that mixes the surface in (``Str``). A ref mixes in the same
surface without becoming a form (``StrRef``). ``Surface`` and the ``Form`` kind
live in ``nu.lang`` (re-exported here for convenience); the NULL queries
(``IsNull``, ``Fallback``) live in ``nu.core``.

Concrete primitive forms live in ``primitives/``, concrete collection forms in
``collections/`` (with the abstract surfaces in ``collections/abc/``).
"""

from nu.lang import Form, Surface

from .collections import (
    Dict,
    DictItems,
    DictItemsSurface,
    DictKeys,
    DictKeysSurface,
    DictSurface,
    DictValues,
    DictValuesSurface,
    FrozenSet,
    FrozenSetSurface,
    Iterator,
    IteratorSurface,
    List,
    ListSurface,
    Set,
    SetSurface,
    Tuple,
    TupleSurface,
)
from .primitives import (
    Bool,
    BoolSurface,
    Bytes,
    BytesSurface,
    Float,
    FloatSurface,
    Int,
    IntSurface,
    None_,
    NoneSurface,
    NullForm,
    NullSurface,
    Object,
    ObjectSurface,
    Str,
    StrSurface,
)


__all__ = [
    "Bool",
    "BoolSurface",
    "Bytes",
    "BytesSurface",
    "Dict",
    "DictItems",
    "DictItemsSurface",
    "DictKeys",
    "DictKeysSurface",
    "DictSurface",
    "DictValues",
    "DictValuesSurface",
    "Float",
    "FloatSurface",
    "Form",
    "FrozenSet",
    "FrozenSetSurface",
    "Int",
    "IntSurface",
    "Iterator",
    "IteratorSurface",
    "List",
    "ListSurface",
    "NoneSurface",
    "None_",
    "NullForm",
    "NullSurface",
    "Object",
    "ObjectSurface",
    "Set",
    "SetSurface",
    "Str",
    "StrSurface",
    "Surface",
    "Tuple",
    "TupleSurface",
]
