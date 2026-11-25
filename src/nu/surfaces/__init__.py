"""Native Surface layer.

A surface is the method layer of a value family (``StrSurface``: ``upper``,
``split``, ``+``, ...), shared by the form node that holds a value
(``nu.forms.Str``) and every ref that holds one (``StrRef``). The atoms the
methods build (``Upper``, ``Append``, ...) live beside their surfaces in the
``*_interactions`` modules. ``Surface`` lives in ``nu.lang`` (re-exported here
for convenience); the NULL queries (``IsNull``, ``Fallback``) live in
``nu.core``.

Primitive surfaces live in ``primitives/``, collection surfaces in
``collections/`` (with the abstract tiers, ``MappingSurface``,
``SequenceSurface``, ..., in ``collections/abc/``). Surfaces never import the
form nodes at import time; a method that returns a node imports it lazily.
"""

from nu.lang import Surface

from .collections import (
    DictItemsSurface,
    DictKeysSurface,
    DictSurface,
    DictValuesSurface,
    FrozenSetSurface,
    IteratorSurface,
    ListSurface,
    SetSurface,
    TupleSurface,
)
from .primitives import (
    BoolSurface,
    BytesSurface,
    FloatSurface,
    IntSurface,
    NoneSurface,
    NullSurface,
    ObjectSurface,
    StrSurface,
)


__all__ = [
    "BoolSurface",
    "BytesSurface",
    "DictItemsSurface",
    "DictKeysSurface",
    "DictSurface",
    "DictValuesSurface",
    "FloatSurface",
    "FrozenSetSurface",
    "IntSurface",
    "IteratorSurface",
    "ListSurface",
    "NoneSurface",
    "NullSurface",
    "ObjectSurface",
    "SetSurface",
    "StrSurface",
    "Surface",
    "TupleSurface",
]
