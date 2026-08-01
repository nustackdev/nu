"""SequenceRef hierarchy — ordered container Ref + Form mixin tiers.

    SequenceRef         = shape.SequenceForm + StructuredRef
    MutableSequenceRef  = shape.MutableSequenceForm + SequenceRef
    ReactiveSequenceRef = shape.ReactiveSequenceForm + MutableSequenceRef

shape.SequenceForm already composes generic SequenceForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Subscript access (``ref[i]``) returns the matching-tier ItemRef.

Form composition provides:
    base:     len(), contains(), iter(), [i], first_elem(), last_elem(), ...,
              exists(), missing(), extract()
    mutable:  + append(v), extend(), insert(i,v), pop(), ..., store(v), erase()
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)

The ``_wrap_*`` abstract methods from SequenceForm are left un-overridden
(raise NotImplementedError) in these blueprints — substrate subclasses fill
them in.
"""

from __future__ import annotations

from nu.domains.shape.forms.sequence import MutableSequenceForm, ReactiveSequenceForm, SequenceForm

from .base import StructuredRef
from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MutableSequenceRef",
    "ReactiveSequenceRef",
    "SequenceRef",
]


class SequenceRef[ItemResultT](SequenceForm, StructuredRef):
    """Ordered container Ref; ``ref[i]`` navigates to the element's child Ref.

    Navigation is defined ONCE (``__getitem__``) and routes through
    ``_wrap_item_ref`` — the child-Ref analogue of ``_wrap_element_result``. Each
    tier supplies the matching domain item Ref as its default; substrates override
    ``_wrap_item_ref`` to return their own item Ref and bind ``ItemResultT`` so
    ``ref[i]`` is statically the correct child Ref type.
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        """Build the child item Ref at ``address``, with self as parent."""
        return ItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]

    def __getitem__(self, index: object) -> ItemResultT:
        """Int index navigates to the child Ref; slice routes to the form-level slice op."""
        if isinstance(index, slice):
            return self.slice(index.start, index.stop, index.step)  # type: ignore[return-value]
        return self._wrap_item_ref(index)


class MutableSequenceRef[ItemResultT](MutableSequenceForm, SequenceRef[ItemResultT]):
    """Mutable ordered container Ref.

    Adds: append(v), extend(), insert(i,v), pop(), ..., store(v), erase().
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return MutableItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]


class ReactiveSequenceRef[ItemResultT](ReactiveSequenceForm, MutableSequenceRef[ItemResultT]):
    """Reactive ordered container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSequenceRef.
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return ReactiveItemRef(address, parent_ref=self, owner_shape=self._owner_shape)  # type: ignore[return-value]
