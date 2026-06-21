"""Native Form layer.

A Form is what a fabric location holds (an Int, a Str, a Dict, a List) and the
fluent typed surface for building Nu over it. The base mixin ``Form`` and the
passthrough ``TypedNu`` live in ``nu2.lang`` (re-exported here for convenience);
the sentinel predicates (``IsEmpty`` / ``IsInvalid``) live in ``nu2.core``.

Concrete primitive Forms live in ``primitives/``, concrete collection Forms in
``collections/`` (with abstract contracts in ``collections/abc/``).
"""

from nu2.lang import Form, TypedNu

from .collections import (
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    FrozenSetForm,
    IteratorForm,
    ListForm,
    SetForm,
    TupleForm,
)
from .primitives import (
    AnyForm,
    BoolForm,
    BytesForm,
    EmptyForm,
    FloatForm,
    IntForm,
    InvalidForm,
    NoneForm,
    SentinelForm,
    StrForm,
)


__all__ = [
    "AnyForm",
    "BoolForm",
    "BytesForm",
    "DictForm",
    "DictItemsForm",
    "DictKeysForm",
    "DictValuesForm",
    "EmptyForm",
    "FloatForm",
    "Form",
    "FrozenSetForm",
    "IntForm",
    "InvalidForm",
    "IteratorForm",
    "ListForm",
    "NoneForm",
    "SentinelForm",
    "SetForm",
    "StrForm",
    "TupleForm",
    "TypedNu",
]
