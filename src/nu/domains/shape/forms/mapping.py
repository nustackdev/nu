"""Shape-domain Mapping Form glue: tier-by-tier composition.

MappingForm         = generic MappingForm + shape CollectionForm
MutableMappingForm  = generic MutableMappingForm + shape MutableCollectionForm
ReactiveMappingForm = generic ReactiveMappingForm + shape MutableMappingForm
                      + shape ReactiveCollectionForm

Each tier composes the matching generic tier with the matching shape tier so the
Ref sees both the full Python-mapping surface AND the shape existence/set/erase
surface via a single base class, with no ItemForm needed in the MRO.

The Reactive tier brings together:
  - ``on_change()``           from generic ReactiveMappingForm (generic)
  - ``on_child_change()`` etc from shape ReactiveCollectionForm (shape-domain)
"""

from __future__ import annotations

from nu.forms.collections.abc.mapping import MappingForm as _MappingForm
from nu.forms.collections.abc.mapping import MutableMappingForm as _MutableMappingForm
from nu.forms.collections.abc.mapping import ReactiveMappingForm as _ReactiveMappingForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MappingForm",
    "MutableMappingForm",
    "ReactiveMappingForm",
]


class MappingForm(_MappingForm, CollectionForm):
    """Shape mapping: key-value ops + exists/missing/extract."""


class MutableMappingForm(_MutableMappingForm, MutableCollectionForm):
    """Mutable shape mapping: key-value ops + exists/missing/extract + set/erase."""


class ReactiveMappingForm(_ReactiveMappingForm, MutableMappingForm, ReactiveCollectionForm):
    """Reactive shape mapping. Adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveMappingForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """
