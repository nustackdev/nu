"""Shape-domain Collection Form chain.

Three tiers:
    CollectionForm          exists(), missing(), extract()
    MutableCollectionForm   + store(), erase()
    ReactiveCollectionForm  + on_child_change(), on_children_change(),
                              on_descendants_change()

These are pure Form mixins — no Ref or substrate knowledge. They sit BETWEEN
the generic collection forms and the concrete Refs, adding shape-domain ops
(existence checks, fabric-level store/erase, tree-aware observation) on top of
whatever generic collection surface the Ref already exposes.

``on_change()`` (observe self) is deliberately absent here — it is generic and
lives on the generic ``ReactiveXxxForm`` tiers in ``nu.forms.collections.abc``,
returning ``nu.core.reactive.OnChangeQuery``. ``ReactiveCollectionForm``
provides only the three tree-aware methods, which reach for the shape-tier
counterparts in ``nu.core.reactive`` too — one unified location for every
reactive query.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.core.reactive import (
        OnChildChangeQuery,
        OnChildrenChangeQuery,
        OnDescendantsChangeQuery,
    )
    from nu.domains.shape.interactions import (
        EraseCommand,
        ExistsQuery,
        ExtractQuery,
        MissingQuery,
        StoreCommand,
    )


__all__ = [
    "CollectionForm",
    "MutableCollectionForm",
    "ReactiveCollectionForm",
]


class CollectionForm(Form):
    """Shape collection — can check existence and extract its subtree."""

    def exists(self) -> ExistsQuery:
        """Return an ExistsQuery — True if this collection slot is bound."""
        from nu.domains.shape.interactions import ExistsQuery

        return ExistsQuery(self)

    def missing(self) -> MissingQuery:
        """Return a MissingQuery — True if this collection slot is unbound."""
        from nu.domains.shape.interactions import MissingQuery

        return MissingQuery(self)

    def extract(self) -> ExtractQuery:
        """Materialise the full subtree rooted at this slot via ExtractQuery."""
        from nu.domains.shape.interactions import ExtractQuery

        return ExtractQuery(self)


class MutableCollectionForm(CollectionForm):
    """Mutable shape collection — read + store + erase."""

    def store(self, value: object) -> StoreCommand:
        """Return a StoreCommand — write ``value`` to this collection slot."""
        from nu.domains.shape.interactions import StoreCommand

        return StoreCommand(self, value)

    def erase(self) -> EraseCommand:
        """Return an EraseCommand — remove this collection slot from the fabric."""
        from nu.domains.shape.interactions import EraseCommand

        return EraseCommand(self)


class ReactiveCollectionForm(MutableCollectionForm):
    """Shape-domain reactive collection — adds tree-aware observation methods.

    Provides (in addition to MutableCollectionForm):
        on_child_change(address)         → OnChildChangeQuery
        on_children_change()             → OnChildrenChangeQuery
        on_descendants_change(*pattern)  → OnDescendantsChangeQuery

    ``on_change()`` (observe self) is intentionally absent — it is generic and
    supplied by the generic ``ReactiveXxxForm`` tier via MRO.
    """

    def on_child_change(self, address: object) -> OnChildChangeQuery:
        """Return an OnChildChangeQuery — subscribe to changes on the child at ``address``."""
        from nu.core.reactive import OnChildChangeQuery

        return OnChildChangeQuery(self, address)

    def on_children_change(self) -> OnChildrenChangeQuery:
        """Return an OnChildrenChangeQuery — subscribe to changes on any immediate child."""
        from nu.core.reactive import OnChildrenChangeQuery

        return OnChildrenChangeQuery(self)

    def on_descendants_change(self, *pattern: object) -> OnDescendantsChangeQuery:
        """Return an OnDescendantsChangeQuery — subscribe to descendants matching ``pattern``."""
        from nu.core.reactive import OnDescendantsChangeQuery

        return OnDescendantsChangeQuery(self, *pattern)
