"""EveryShape collections module.

This module provides a common types, interfaces and set of behaviors for various common collections.
"""

from __future__ import annotations

from .capabilities import (
    Appendable,
    Assignable,
    ChildObservable,
    Clearable,
    Containable,
    Convertible,
    Deletable,
    DescendantsObservable,
    Initializable,
    Nestable,
    Observable,
    Sizeable,
    Subscriptable,
    is_appendable,
    is_assignable,
    is_child_observable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_descendants_observable,
    is_initializable,
    is_nestable,
    is_observable,
    is_sizeable,
    is_subscriptable,
)
from .collections import (
    Collection,
    Container,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)


__all__ = [  # noqa: RUF022
    # Capabilities
    "Appendable",
    "Assignable",
    "ChildObservable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "DescendantsObservable",
    "Initializable",
    "Nestable",
    "Observable",
    "Sizeable",
    "Subscriptable",
    "is_appendable",
    "is_assignable",
    "is_child_observable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_descendants_observable",
    "is_initializable",
    "is_nestable",
    "is_observable",
    "is_sizeable",
    "is_subscriptable",
    # Collection protocols
    "Collection",
    "Container",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
]
