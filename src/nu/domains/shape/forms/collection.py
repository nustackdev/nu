"""Shape-domain Collection Form chain.

Three tiers:
    CollectionForm          exists(), missing(), extract()
    MutableCollectionForm   + store(), erase()
    ReactiveCollectionForm  + on_child_change(), on_children_change(),
                              on_descendants_change()

These are pure Form mixins — no Ref or substrate knowledge. They sit BETWEEN
the generic collection forms and the concrete Refs, adding shape-domain ops
(existence checks, fabric-level set/erase, tree-aware observation) on top of
whatever generic collection surface the Ref already exposes.

``on_change()`` (observe self) is deliberately absent here — it is generic and
lives on the generic ``ReactiveXxxForm`` tiers in ``nu.forms.collections.abc``,
returning ``nu.core.reactive.OnChange``. ``ReactiveCollectionForm``
provides only the three tree-aware methods, which reach for the shape-tier
counterparts in ``nu.core.reactive`` too — one unified location for every
reactive query.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.core.reactive import (
        OnChildChange,
        OnChildrenChange,
        OnDescendantsChange,
    )
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Extract,
        Missing,
        SetCmd,
    )


__all__ = [
    "CollectionForm",
    "MutableCollectionForm",
    "ReactiveCollectionForm",
]


class CollectionForm(Form):
    """Shape collection — can check existence and extract its subtree."""

    def exists(self) -> Exists:
        """Return an Exists — True if this collection slot is bound."""
        from nu.domains.shape.interactions import Exists

        return Exists(self)

    def missing(self) -> Missing:
        """Return a Missing — True if this collection slot is unbound."""
        from nu.domains.shape.interactions import Missing

        return Missing(self)

    def extract(self) -> Extract:
        """Materialise the full subtree rooted at this slot via Extract."""
        from nu.domains.shape.interactions import Extract

        return Extract(self)


class MutableCollectionForm(CollectionForm):
    """Mutable shape collection — read + store + erase."""

    def set(self, value: object) -> SetCmd:
        """Return a SetCmd — write ``value`` to this collection slot."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Return an Erase — remove this collection slot from the fabric."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)


class ReactiveCollectionForm(MutableCollectionForm):
    """Shape-domain reactive collection — adds tree-aware observation methods.

    Provides (in addition to MutableCollectionForm):
        on_child_change(address)         → OnChildChange
        on_children_change()             → OnChildrenChange
        on_descendants_change(*pattern)  → OnDescendantsChange

    ``on_change()`` (observe self) is intentionally absent — it is generic and
    supplied by the generic ``ReactiveXxxForm`` tier via MRO.
    """

    def on_child_change(self, address: object) -> OnChildChange:
        """Return an OnChildChange — subscribe to changes on the child at ``address``."""
        from nu.core.reactive import OnChildChange

        return OnChildChange(self, address)

    def on_children_change(self) -> OnChildrenChange:
        """Return an OnChildrenChange — subscribe to changes on any immediate child."""
        from nu.core.reactive import OnChildrenChange

        return OnChildrenChange(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChange:
        """Return an OnDescendantsChange — subscribe to descendants matching ``pattern``."""
        from nu.core.reactive import OnDescendantsChange

        return OnDescendantsChange(self, *pattern)
