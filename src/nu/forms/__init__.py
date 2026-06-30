"""Native Form layer.

A Form is what a fabric location holds (an Int, a Str, a Dict, a ListQuery) and the
fluent typed surface for building Nu over it. The base mixin ``Form`` and the
passthrough ``TypedNu`` live in ``nu.lang`` (re-exported here for convenience);
the sentinel predicates (``IsEmptyQuery`` / ``IsInvalidQuery``) live in ``nu.core``.

Concrete primitive Forms live in ``primitives/``, concrete collection Forms in
``collections/`` (with abstract contracts in ``collections/abc/``).
"""

from nu.lang import Form, TypedNu

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
