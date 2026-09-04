"""Shape-domain Collection Form chain.

Three tiers:
    CollectionForm          exists(), missing(), extract()
    MutableCollectionForm   + set(), erase()
    ReactiveCollectionForm  + on_child_change(), on_children_change(),
                              on_descendants_change()

Pure Form mixins: no Ref or substrate knowledge. They sit BETWEEN
the generic collection forms and the concrete Refs, adding shape-domain ops
(existence checks, fabric-level set/erase, tree-aware observation) on top of
whatever generic collection surface the Ref already exposes.

``on_change()`` (observe self) is deliberately absent here. It is generic and
lives on the generic ``ReactiveXxxForm`` tiers in ``nu.forms.collections.abc``,
returning ``nu.reactive.OnChange``. ``ReactiveCollectionForm``
provides only the three tree-aware methods, which reach for the shape-tier
counterparts in ``nu.reactive`` too: one unified location for every
reactive query.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Extract,
        Missing,
        SetCmd,
    )
    from nu.flows.control import IfDo
    from nu.reactive import (
        OnChildChange,
        OnChildrenChange,
        OnDescendantsChange,
    )


__all__ = [
    "CollectionForm",
    "MutableCollectionForm",
    "ReactiveCollectionForm",
]


class CollectionForm(Form):
    """Shape collection Form. Ops: ``exists()``, ``missing()``, ``extract()``."""

    def exists(self) -> Exists:
        """Build an ``Exists`` query."""
        from nu.domains.shape.interactions import Exists

        return Exists(self)

    def missing(self) -> Missing:
        """Build a ``Missing`` query."""
        from nu.domains.shape.interactions import Missing

        return Missing(self)

    def extract(self) -> Extract:
        """Build an ``Extract`` query."""
        from nu.domains.shape.interactions import Extract

        return Extract(self)


class MutableCollectionForm(CollectionForm):
    """Mutable shape collection Form. Adds ``set(value)`` and ``erase()``."""

    def set(self, value: object) -> SetCmd:
        """Build a ``SetCmd``."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Build an ``Erase``."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)

    def init(self, value: object) -> IfDo:
        """Set ``value`` iff the collection is currently missing."""
        from nu.flows.control import IfDo

        return IfDo(self.missing(), self.set(value))


class ReactiveCollectionForm(MutableCollectionForm):
    """Reactive shape collection Form. Adds tree-aware observation.

    Ops:
        on_child_change(address)         -> OnChildChange
        on_children_change()             -> OnChildrenChange
        on_descendants_change(*pattern)  -> OnDescendantsChange

    ``on_change()`` (observe self) is intentionally absent. It is generic and
    supplied by the generic ``ReactiveXxxForm`` tier via MRO.
    """

    def on_child_change(self, address: object) -> OnChildChange:
        """Observe changes at a specific child address."""
        from nu.reactive import OnChildChange

        return OnChildChange(self, address)

    def on_children_change(self) -> OnChildrenChange:
        """Observe changes across all direct children."""
        from nu.reactive import OnChildrenChange

        return OnChildrenChange(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChange:
        """Observe changes across descendants matching ``pattern``."""
        from nu.reactive import OnDescendantsChange

        return OnDescendantsChange(self, *pattern)
