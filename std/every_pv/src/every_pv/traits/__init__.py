"""Storage access traits for PV refs.

Traits define what storage operations a ref supports. They are mixins that
provide methods for interacting with PV storage.

Hierarchy:
    CORE TRAITS
    -----------
    ExistableBase      →  exists(), missing()
    GettableBase       →  get()
    SettableBase       →  set()
    DeletableBase      →  remove()
    ClearableBase      →  clear()
    LengthableBase     →  length()
    StorableBase       →  store()
    CollectionGettableBase  →  get() for containers

    SEQUENCE TRAITS
    ---------------
    SequenceIndexableBase  →  __getitem__ (index/slice)
    SequenceIterableBase   →  map(), filter(), reduce(), find(), find_index(), index(), count()
    AppendableBase         →  append()
    InsertableBase         →  insert()
    PoppableBase           →  pop()

    MAPPING TRAITS
    --------------
    MappingNestableBase    →  __getitem__ (key navigation)
    MappingIterableBase    →  map_values(), map_items(), filter(), reduce(), find_key(), find_value(), find_item()
    MappingAccessibleBase  →  get_item(), set_item(), remove_item()

    SET TRAITS
    ----------
    SetAddableBase         →  add()
    SetRemovableBase       →  remove(), discard()

    QUERY TRAITS
    ------------
    KeysQueryableBase      →  keys()
    ValuesQueryableBase    →  values()
    ItemsQueryableBase     →  items()

    OBSERVABLE TRAITS
    -----------------
    PrimitiveObservableBase  →  on_change()
    ViewObservableBase       →  on_change(), on_child_change(), on_children_change(), on_descendants_change()
"""

from __future__ import annotations

# Core traits
from .core import (
    ClearableBase,
    CollectionGettableBase,
    DeletableBase,
    ExistableBase,
    ExtractableBase,  # Alias for CollectionGettableBase
    GettableBase,
    LengthableBase,
    SettableBase,
    StorableBase,
)

# Mapping traits
from .mapping import (
    MappingAccessibleBase,
    MappingIterableBase,
    MappingNestableBase,
)

# Observable traits
from .observable import (
    PrimitiveObservableBase,
    ViewObservableBase,
)

# Query traits
from .query import (
    ItemsQueryableBase,
    KeysQueryableBase,
    ValuesQueryableBase,
)

# Sequence traits
from .sequence import (
    AppendableBase,
    InsertableBase,
    PoppableBase,
    SequenceIndexableBase,
    SequenceIterableBase,
)

# Set traits
from .set import (
    SetAddableBase,
    SetRemovableBase,
)


__all__ = [  # noqa: RUF022
    # Core traits
    "ExistableBase",
    "GettableBase",
    "SettableBase",
    "DeletableBase",
    "ClearableBase",
    "LengthableBase",
    "StorableBase",
    "CollectionGettableBase",
    "ExtractableBase",  # Alias for backwards compat
    # Sequence traits
    "SequenceIndexableBase",
    "SequenceIterableBase",
    "AppendableBase",
    "InsertableBase",
    "PoppableBase",
    # Mapping traits
    "MappingNestableBase",
    "MappingIterableBase",
    "MappingAccessibleBase",
    # Set traits
    "SetAddableBase",
    "SetRemovableBase",
    # Query traits
    "KeysQueryableBase",
    "ValuesQueryableBase",
    "ItemsQueryableBase",
    # Observable traits
    "PrimitiveObservableBase",
    "ViewObservableBase",
]
