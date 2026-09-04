"""Reactive change subscriptions -- unified interaction atoms.

Five queries, one place. Every reactive subscription in Nu -- generic Form
observation, tree-aware shape observation, and substrate-leaf observation --
lives here so callers reach for one namespace regardless of what they hold.

- ``OnChange``            -- ``view.on_change()``. Subscribe to any change
                                  on the slot-0 Ref's view (collection- and
                                  view-tier Refs; the Ref must yield an
                                  observable view).
- ``OnChildChange``       -- ``view.on_child_change(address)``. Subscribe
                                  to changes on one specific child of the
                                  slot-0 Ref's view. Slot 1 is the address.
- ``OnChildrenChange``    -- ``view.on_children_change()``. Subscribe to
                                  changes on all immediate children.
- ``OnDescendantsChange`` -- ``view.on_descendants_change(*pattern)``.
                                  Subscribe to descendants matching a pattern.
                                  Slots 1.. are the pattern segments.
- ``OnPrimitiveChange``   -- leaf variant. A leaf Ref yields a scalar
                                  value, not a view, so it subscribes on its
                                  *parent* view's child-change channel keyed by
                                  the leaf's own address. Slot 0 is the leaf
                                  Ref; the query calls ``ref._afetch_parent``
                                  and ``ref._aaddress`` at runtime, so the
                                  substrate needs to implement those (any
                                  ``StructuredRef`` substrate that provides
                                  navigation already does).

View methods return an opaque ``options`` value -- a pure filter descriptor,
no observer coupling. Each query resolves the process-scope
``ObserverProtocol`` from ctx and calls ``observer.subscribe(options)``.

Sentinel handling. If the underlying view resolves to ``EMPTY`` / ``INVALID``
(the address is unbound, the intermediate container is missing), the
subscription cannot be created and the query yields ``INVALID`` -- consistent
with the rest of ``nu.core``.

Sync path. Building a real subscription requires calling into an Observer,
which is a lifecycle-managed resource that lives inside an async runtime.
The sync ``_compile`` paths raise ``RuntimeError`` to make the boundary
loud rather than silently returning stale options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core.reactive.protocol import ObserverProtocol
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
]


_SYNC_UNSUPPORTED = (
    "Reactive subscription queries require an async runtime "
    "(the process-scope Observer is async-lifecycle managed). "
    "Use nu.arun(...) instead of nu.run(...)."
)


class OnChange(ScalarQuery):
    """Opens a subscription to any change on a Ref's view.

    Args:
        ref: a collection- or view-tier Ref. Must yield an observable view,
            i.e. one that answers ``on_change()``.

    Notes:
        - Async only. The sync path raises ``RuntimeError`` rather than
          returning options without an observer behind them; use ``nu.arun``.
        - ``view.on_change()`` returns opaque filter options, nothing
          observer-bound. The atom resolves the process-scope
          ``ObserverProtocol`` from ctx and hands the options to
          ``subscribe`` unread - Nu never inspects a backend's filter dialect.
        - Subscribing reads no value off the view, so nothing here recomputes
          on change. The handle only delivers notifications to receivers bound
          on it; ``React`` / ``ReactWhile`` / ``ReactForever`` are what bind
          them and run a body.
        - Fires on any mutation reaching that view, with no distinction of
          which mutation it was.
        - Each evaluation opens a fresh subscription; whoever binds a receiver
          is responsible for closing it.

    Yields:
        The ``Subscription`` handle from ``observer.subscribe(options)``.
        INVALID when the view resolves to EMPTY or INVALID (unbound address,
        missing intermediate container) - no subscription is opened.

    Example:
        nu.arun(nu.ReactForever(users.on_change(), body))
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class OnChildChange(ScalarQuery):
    """Opens a subscription to changes on one named child of a Ref's view.

    Args:
        ref: a structured Ref. Must yield a view that answers
            ``on_child_change(address)``.
        address: the child to watch, as a key or index the view understands.

    Notes:
        - Async only. The sync path raises ``RuntimeError``; use ``nu.arun``.
        - ``address`` is evaluated only after the view resolves, so a sentinel
          view short-circuits without touching it.
        - Watches that one child slot, not the subtree under it.
        - The atom resolves the process-scope ``ObserverProtocol`` from ctx and
          passes the view's opaque options through to ``subscribe`` unread.
        - Each evaluation opens a fresh subscription; the binder closes it.

    Yields:
        The ``Subscription`` handle from ``observer.subscribe(options)``.
        INVALID when either the view or the address is EMPTY or INVALID - no
        subscription is opened.

    Example:
        nu.arun(nu.React(users.on_child_change("alice"), body))
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class OnChildrenChange(ScalarQuery):
    """Opens a subscription to changes on any immediate child of a Ref's view.

    Args:
        ref: a structured Ref. Must yield a view that answers
            ``on_children_change()``.

    Notes:
        - Async only. The sync path raises ``RuntimeError``; use ``nu.arun``.
        - Covers the immediate children only. Anything deeper needs
          ``OnDescendantsChange``.
        - The atom resolves the process-scope ``ObserverProtocol`` from ctx and
          passes the view's opaque options through to ``subscribe`` unread.
        - Each evaluation opens a fresh subscription; the binder closes it.

    Yields:
        The ``Subscription`` handle from ``observer.subscribe(options)``.
        INVALID when the view is EMPTY or INVALID - no subscription is opened.

    Example:
        nu.arun(nu.ReactForever(users.on_children_change(), body))
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class OnDescendantsChange(ScalarQuery):
    """Opens a subscription to descendants of a Ref's view matching a pattern.

    Args:
        ref: a structured Ref. Must yield a view that answers
            ``on_descendants_change(p0, p1, ...)``.
        *pattern: the path segments to match descendants against, in order.
            Their meaning (wildcards and all) belongs to the backend.

    Notes:
        - Async only. The sync path raises ``RuntimeError``; use ``nu.arun``.
        - At least one pattern segment is required, and the check happens at
          evaluation, not at construction: an empty pattern raises
          ``ValueError`` from the running thunk.
        - Segments are evaluated in order, after the view, and any sentinel
          among them collapses the whole subscription rather than being
          dropped from the pattern.
        - The atom resolves the process-scope ``ObserverProtocol`` from ctx and
          passes the view's opaque options through to ``subscribe`` unread.
        - Each evaluation opens a fresh subscription; the binder closes it.

    Yields:
        The ``Subscription`` handle from ``observer.subscribe(options)``.
        INVALID when the view or any pattern segment is EMPTY or INVALID - no
        subscription is opened.

    Example:
        nu.arun(nu.ReactForever(users.on_descendants_change("*", "email"), body))
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class OnPrimitiveChange(ScalarQuery):
    """Opens a subscription to changes at a leaf Ref, through its parent view.

    A leaf Ref yields a scalar, not a view, so there is no ``on_change()`` to
    call on it. This atom goes one level up instead: it asks the leaf for its
    parent view and its own address, and subscribes on the parent's
    child-change channel keyed by that address. Every substrate whose Refs
    implement ``_afetch_parent`` and ``_aaddress`` - all structured refs -
    gets leaf reactivity from this one path, with nothing to override per
    substrate.

    Args:
        ref: the leaf Ref to watch.

    Notes:
        - Async only. The sync path raises ``RuntimeError``; use ``nu.arun``.
        - The leaf's own thunk is never driven. Path knowledge is read off the
          Ref instance and its child nid, so subscribing does not read the
          leaf's value and records no dependency on it.
        - Notifications ride the parent's child-change channel, so the atom
          sees whatever that channel reports for the address, including the
          leaf appearing or being deleted.
        - Each evaluation opens a fresh subscription; the binder closes it.

    Yields:
        The ``Subscription`` handle from ``observer.subscribe(options)``.
        INVALID when the parent view or the address is EMPTY or INVALID, which
        is what a leaf under a missing container gives - no subscription is
        opened.

    Example:
        nu.arun(nu.React(user["email"].on_change(), body))
    """

    def __init__(self, ref: object) -> None:
        # Slot 0 holds the leaf Ref directly; its own compiled thunk is not
        # driven -- we read path knowledge off the Ref instance and its child
        # nid.
        super().__init__(ref)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        del nid, children

        def thunk(rt: Runtime) -> object:
            del rt
            raise RuntimeError(_SYNC_UNSUPPORTED)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
