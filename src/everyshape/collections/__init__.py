"""EveryShape collections module.

This module provides a common types, interfaces and set of behaviors for various common collections.
"""

from __future__ import annotations

from .capabilities import (
    Appendable,
    Assignable,
    ChildWatchable,
    Clearable,
    Containable,
    Convertible,
    Deletable,
    Initializable,
    Nestable,
    Sizeable,
    Subscriptable,
    Watchable,
    is_appendable,
    is_assignable,
    is_child_watchable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_initializable,
    is_nestable,
    is_sizeable,
    is_subscriptable,
    is_watchable,
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
    "ChildWatchable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "Initializable",
    "Nestable",
    "Sizeable",
    "Subscriptable",
    "Watchable",
    "is_appendable",
    "is_assignable",
    "is_child_watchable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_initializable",
    "is_nestable",
    "is_sizeable",
    "is_subscriptable",
    "is_watchable",
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
