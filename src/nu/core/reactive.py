"""Reactive change subscriptions -- unified core interface.

Five queries, one place. Every reactive subscription in Nu -- generic Form
observation, tree-aware shape observation, and substrate-leaf observation --
lives here so callers reach for one namespace regardless of what they hold.

- ``OnChangeQuery``            -- ``view.on_change()``. Subscribe to any change
                                  on the slot-0 Ref's view (collection- and
                                  view-tier Refs; the Ref must yield an
                                  observable view).
- ``OnChildChangeQuery``       -- ``view.on_child_change(address)``. Subscribe
                                  to changes on one specific child of the
                                  slot-0 Ref's view. Slot 1 is the address.
- ``OnChildrenChangeQuery``    -- ``view.on_children_change()``. Subscribe to
                                  changes on all immediate children.
- ``OnDescendantsChangeQuery`` -- ``view.on_descendants_change(*pattern)``.
                                  Subscribe to descendants matching a pattern.
                                  Slots 1.. are the pattern segments.
- ``OnPrimitiveChangeQuery``   -- leaf variant. A leaf Ref yields a scalar
                                  value, not a view, so it subscribes on its
                                  *parent* view's child-change channel keyed by
                                  the leaf's own address. Slot 0 is the leaf
                                  Ref; the query calls ``ref._afetch_parent``
                                  and ``ref._aaddress`` at runtime, so the
                                  substrate needs to implement those (any
                                  ``StructuredRef`` substrate that provides
                                  navigation already does).

Post-split (virtuals publisher/observer split): view methods return
``SubscriptionOptions`` -- pure filter descriptors, no observer coupling.
Each query resolves the process-scope ``ObserverProtocol`` from ctx and
calls ``observer.subscribe(options)`` to obtain the ``Subscription``.

Sentinel handling. If the underlying view resolves to ``EMPTY`` / ``INVALID``
(the address is unbound, the intermediate container is missing), the
subscription cannot be created and the query yields ``INVALID`` -- consistent
with the rest of ``nu.core``.

Sync path. Building a real subscription requires calling into an Observer,
which is a lifecycle-managed resource that lives inside an async runtime.
The sync ``_compile`` paths raise ``RuntimeError`` to make the boundary
loud rather than silently returning stale ``SubscriptionOptions``.

Naming. v1 called these ``OnChange`` / ``OnChildChange`` / ``OnChildrenChange``
/ ``OnDescendantsChange`` / ``OnPrimitiveChangeOp``; v2 adds the ``Query``
suffix for the atom-class convention. The interface (arity, method call, yield
value) is unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID
from virtuals.tkv.observer import ObserverProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "OnChangeQuery",
    "OnChildChangeQuery",
    "OnChildrenChangeQuery",
    "OnDescendantsChangeQuery",
    "OnPrimitiveChangeQuery",
]


_SYNC_UNSUPPORTED = (
    "Reactive subscription queries require an async runtime "
    "(the process-scope Observer is async-lifecycle managed). "
    "Use nu.arun(...) instead of nu.run(...)."
)


class OnChangeQuery(ScalarQuery):
    """Subscribe to any change on the slot-0 Ref's view.

    Slot 0 must yield an observable view (a collection- or view-tier Ref).
    Returns the ``Subscription`` handle from ``observer.subscribe(options)``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid
        view_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            options = view.on_change()
            observer = rt.ctx.get(ObserverProtocol)
            return observer.subscribe(options)

        return athunk


class OnChildChangeQuery(ScalarQuery):
    """Subscribe to changes on one specific child of the slot-0 Ref's view.

    Children: ``[ref, address]``. Slot 0 must yield a view that supports
    ``on_child_change(address)`` (a structured Ref's view); slot 1 resolves to
    the child address.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid
        view_thunk, address_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            address = await address_thunk(rt)
            if address is EMPTY or address is INVALID:
                return INVALID
            options = view.on_child_change(address)
            observer = rt.ctx.get(ObserverProtocol)
            return observer.subscribe(options)

        return athunk


class OnChildrenChangeQuery(ScalarQuery):
    """Subscribe to changes on all immediate children of the slot-0 Ref's view.

    Slot 0 must yield a view that supports ``on_children_change()``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid
        view_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            options = view.on_children_change()
            observer = rt.ctx.get(ObserverProtocol)
            return observer.subscribe(options)

        return athunk


class OnDescendantsChangeQuery(ScalarQuery):
    """Subscribe to descendants matching a pattern on the slot-0 Ref's view.

    Children: ``[ref, pattern_0, pattern_1, ...]``. At least one pattern child
    is required. Slot 0 must yield a view that supports
    ``on_descendants_change(p0, p1, ...)``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid
        view_thunk = children[0]
        pattern_thunks = children[1:]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            if not pattern_thunks:
                raise ValueError("Pattern cannot be empty for on_descendants_change")
            pattern = []
            for pt in pattern_thunks:
                p = await pt(rt)
                if p is EMPTY or p is INVALID:
                    return INVALID
                pattern.append(p)
            options = view.on_descendants_change(pattern[0], *pattern[1:])
            observer = rt.ctx.get(ObserverProtocol)
            return observer.subscribe(options)

        return athunk


class OnPrimitiveChangeQuery(ScalarQuery):
    """Subscribe to changes at a leaf Ref's address within its parent view.

    A leaf Ref yields a scalar value, not a view, so ``OnChangeQuery`` (which
    calls ``view.on_change()``) does not apply. The subscription happens on the
    *parent* view's child-change channel keyed by the leaf's own address.

    Children: ``[ref]``. At runtime the query calls ``ref._afetch_parent(rt,
    ref_nid)`` to obtain the parent view and ``ref._aaddress(rt, ref_nid)`` to
    resolve the address, then returns ``observer.subscribe(options)``.

    Every substrate whose Refs implement ``_afetch_parent`` (all structured
    refs) picks this up for free -- no per-substrate override needed.
    """

    def __init__(self, ref: object) -> None:
        # Slot 0 holds the leaf Ref directly; its own compiled thunk is not
        # driven -- we read path knowledge off the Ref instance and its child
        # nid.
        super().__init__(ref)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            ref_nid = rt.program.children[nid][0]
            parent = await ref._afetch_parent(rt, ref_nid)
            if parent is EMPTY or parent is INVALID:
                return INVALID
            address = await ref._aaddress(rt, ref_nid)
            if address is EMPTY or address is INVALID:
                return INVALID
            options = parent.on_child_change(address)
            observer = rt.ctx.get(ObserverProtocol)
            return observer.subscribe(options)

        return athunk
