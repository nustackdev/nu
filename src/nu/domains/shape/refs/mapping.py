"""MappingRef hierarchy — key-value container Ref + Form mixin tiers.

    MappingRef         = shape.MappingForm + StructuredRef
    MutableMappingRef  = shape.MutableMappingForm + MappingRef
    ReactiveMappingRef = shape.ReactiveMappingForm + MutableMappingRef

Navigation (``ref[key]``) is defined ONCE here and routes through the
``_wrap_item_ref`` hook — the child-Ref analogue of ``_wrap_value_result`` /
``_wrap_keys_result``. Each substrate provides ``_wrap_item_ref`` (building its
own item Ref) instead of re-overriding ``__getitem__``, and binds the
``ItemResultT`` type parameter so ``ref[key]`` is statically the correct child
Ref type. The blueprint leaves ``_wrap_item_ref`` abstract (like the other wrap
hooks), so a substrate that forgets it is a loud NotImplementedError, not a
silently broken domain Ref.
"""

from __future__ import annotations

from nu.domains.shape.forms.mapping import MappingForm, MutableMappingForm, ReactiveMappingForm

from .base import StructuredRef
from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MappingRef",
    "MutableMappingRef",
    "ReactiveMappingRef",
]


class MappingRef[ItemResultT](MappingForm, StructuredRef):
    """Key-value container Ref; ``ref[key]`` navigates to the value's child Ref.

    Navigation is defined ONCE (``__getitem__``) and routes through
    ``_wrap_item_ref`` — the child-Ref analogue of ``_wrap_value_result``. Each
    tier supplies the matching domain item Ref as its default; substrates override
    ``_wrap_item_ref`` to return their own substrate-backed item Ref and bind
    ``ItemResultT`` so ``ref[key]`` is statically the correct child Ref type.
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        """Build the child item Ref at ``address``, with self as parent."""
        return ItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]

    def __getitem__(self, key: object) -> ItemResultT:
        """Navigate to the child Ref at ``key``, with self as parent."""
        return self._wrap_item_ref(key)


class MutableMappingRef[ItemResultT](MutableMappingForm, MappingRef[ItemResultT]):
    """Mutable key-value container Ref.

    Adds: set(k,v), delete(k), update(), store(v), erase() on top of MappingRef.
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return MutableItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]


class ReactiveMappingRef[ItemResultT](ReactiveMappingForm, MutableMappingRef[ItemResultT]):
    """Reactive key-value container Ref.

    Adds: on_change() (generic), on_child_change(), on_children_change(),
    on_descendants_change() (shape-domain) on top of MutableMappingRef.
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return ReactiveItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]
