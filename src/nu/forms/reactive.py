"""Generic Form-level reactive observation query.

This is Form-layer infrastructure, not a shape-domain concept. Any Form that
carries a live slot can expose change subscriptions through this query.

- ``OnChangeQuery``  subscribe to all changes on slot 0.

The three tree-aware queries (OnChildChangeQuery, OnChildrenChangeQuery,
OnDescendantsChangeQuery) are shape-domain: they require structured Refs with
the child/children/descendants concept. They live in
``nu.domains.shape.interactions``.

Materialising a subscription registers an observer in the substrate's observer
registry. The observed Ref's data is untouched — this is a ``ScalarQuery``, not
a ``ScalarAction``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "OnChangeQuery",
]


class OnChangeQuery(ScalarQuery):
    """Subscribe to changes at the slot-0 Ref; yield the Subscription handle."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            view = view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            return view.on_change()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            return view.on_change()

        return athunk
