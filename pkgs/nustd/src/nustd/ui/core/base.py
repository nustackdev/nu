"""Generic UI Ref -- host-independent base for the widget kit.

A Ref is a Nu Ref whose storage is a client rendering surface (a browser
tab, in nudle's case). `_wire_type` is the identifier the client uses to
pick a renderer; the methods a Ref exposes (`set`, `append`, `on_change`,
...) decide which interactions it accepts.

Built on `StructuredRef` (parent chain, `_root_shape`). Address
resolution walks the on-tree parent chain and returns the segments as a
tuple, same as `nustd.kv` does. Nothing outside the chain gets a say: a
segment is in the address because something navigated through it, never
because a class named itself. A Section contributes its segment by being
reached through the slot that declares it. Async-only: nustd.ui is a
browser fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.domains.shape.base import StructuredRef
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.domains.shape.dsl import Shape
    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Ref"]


def _wire_type_of(ref_or_section_cls: type) -> str:
    """Browser component a Ref or Section class renders as.

    A plain attribute read, no search. Every Ref the kit ships declares its
    own ``_wire_type``, and a user subclass (``class Label(TextRef)``)
    inherits it the ordinary Python way, so it reports ``TextRef`` and the
    browser registry resolves it. Out-of-tree Refs that register their own
    component declare the ClassVar too; that is the whole mechanism, there is
    no separate escape hatch.

    A Section draws as the container Ref behind it, so one that declares no
    wire type of its own reports its ``_ref_cls``'s: shipped Shapes declare
    nothing and ``class Toolbar(Row)`` reports ``Row`` by way of ``RowRef``.
    The attribute is read with ``getattr`` because this module sits under
    ``section.py`` and cannot import it. Anything that still has nothing to
    report (a user ``class Fancy(Section)`` on bare ``SectionRef``) falls back
    to its own class name.
    """
    declared = getattr(ref_or_section_cls, "_wire_type", "")
    if declared:
        return declared
    ref_cls = getattr(ref_or_section_cls, "_ref_cls", None)
    from_ref = getattr(ref_cls, "_wire_type", "") if ref_cls is not None else ""
    return from_ref or ref_or_section_cls.__name__


def _level_type(term: object) -> str:
    """Wire type the browser renders this level with.

    A SectionRef is substrate: what the browser draws is the Section class
    it carries, same as the boot batch reports. Everything else is the
    ref class itself.
    """
    section_cls = getattr(term, "_payload", {}).get("section_cls")
    return _wire_type_of(section_cls if section_cls is not None else type(term))


class Ref(StructuredRef):
    """Base for Refs backed by a client rendering surface. Async-only.

    A Ref with a single semantically primary value exposes `set()` for it
    (`TextRef.set(text)`, `SliderRef.set(n)`); everything else it can drive
    gets its own `set_*`. A container has no primary value, so it has no
    `set()` at all -- see the `nustd.ui.refs` package docstring.
    """

    _requires_async = Declared(value=True, name="requires_async")

    # Browser component this Ref renders as. Every Ref the kit ships declares
    # its own; subclasses inherit it, which is how a user subclass renders as
    # its nearest shipped ancestor. Empty means "fall back to the class name".
    _wire_type: ClassVar[str] = ""

    # A leaf draws one thing from its own props and never has children. Only
    # the kit's leaves (``LeafRef``) set it: a plain Ref, a SectionRef and a
    # host's own Refs keep taking children, since a host may hang a channel
    # or a region off anything it mounts.
    _leaf: ClassVar[bool] = False

    def __init__(
        self,
        address: object,
        *,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
        props: Mapping[str, object] | None = None,
    ) -> None:
        if isinstance(parent_ref, Ref) and type(parent_ref)._leaf:
            leaf = type(parent_ref).__name__
            msg = (
                f"{leaf} is a leaf and holds no children; put {address!r} in a "
                "container (Column, Row, Card, ...)"
            )
            raise TypeError(msg)
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        # State lives in ``payload`` (part of the Term identity) so the base
        # ``Term._with_children`` carries it across a tree rewrite -- no override.
        self._payload["segment"] = address
        if props is not None:
            # A Ref built alone carries what its slot would have declared: the
            # same normalizer and the same defaults, so the browser cannot tell
            # ``RowRef("r", parent_ref=card, props=...)`` from a declared slot.
            self._payload["props"] = dict(type(self).slot(**props).props)

    # --- wire-path resolution ------------------------------------------------

    async def _aresolve_address(self, rt: Runtime, nid: int) -> tuple[str, ...]:
        """Wire path for this Ref: the chain's segments, root-first.

        Walks the on-tree parent chain (``rt.program.children``: ``[0]`` =
        structural parent, ``[1]`` = address) and evaluates each level's
        address child, so a computed segment resolves here like any other
        child. Self plus parents is the whole address; nothing else feeds it.
        """
        segments: list[str] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            segments.append(str(await rt.aeval(kids[1])))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        segments.reverse()
        return tuple(segments)

    async def _aresolve_chain(self, rt: Runtime, nid: int) -> tuple[tuple[str, str, dict], ...]:
        """Same walk as ``_aresolve_address``, annotated per level.

        Returns ``(segment, type, props)`` root-first, one entry per level.
        The term at each level *is* the ref, so its wire type and the props
        its slot declared come straight off it -- no second traversal. The
        browser needs all three to create a component on first write instead
        of being told about it up front.
        """
        levels: list[tuple[str, str, dict]] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            term = rt.program.terms[cur]
            segment = str(await rt.aeval(kids[1]))
            props = dict(getattr(term, "_payload", {}).get("props") or {})
            levels.append((segment, _level_type(term), props))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        levels.reverse()
        return tuple(levels)

    # --- execution (async-only) ----------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Any:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            raise NotImplementedError(
                f"{type(self).__name__} is display-only; reading is not supported",
            )

        return athunk

    async def _aread(self, rt: Runtime, nid: int) -> Any:
        """Round-trip read of the live client value (input Refs override _acompile)."""
        from .session import Session

        session = rt.ctx.fabrics.get(Session)
        path = await self._aresolve_address(rt, nid)
        return self._lift(await session.aread(path))

    # --- interactions --------------------------------------------------------

    def erase(self) -> Nu:
        """Drop this Ref's node on the client, and everything under it.

        On every Ref, not on a chosen few: what goes away is the address, and
        any Ref has one. On a container it takes the whole subtree, which is
        how something that redraws from scratch clears what its last run left.

        Nothing has to be put back by hand -- the next write carries the chain,
        so the node comes back with its declared type and props the moment
        anything is written to it again.

        ``erase``, ``init``, ``hide``, ``display`` and ``showing`` are
        methods on every Ref, so each hides a Shape slot of the same name:
        name no slot after them.
        """
        from .interactions import Remove

        return Remove(self)

    def init(self) -> Nu:
        """Put this Ref's node on screen as declared, and every slot its Shape declares.

        For a node whose look and content are all props (a heading, a card,
        a page built from Refs): it shows without a write restating them.
        Writes that come later land on it as usual.
        """
        from .interactions import Init

        return Init(self)

    def hide(self) -> Nu:
        """Take this Ref's node off screen, and its whole subtree, keeping their state.

        ``display`` brings them back as they were. A node hidden before
        anything wrote it is created hidden, so a panel can start out of
        sight. A child under a hidden node stays off screen whatever is sent
        to the child itself.
        """
        from .interactions import Hide

        return Hide(self)

    def display(self) -> Nu:
        """Put this Ref's node back on screen after ``hide``, with its subtree."""
        from .interactions import Display

        return Display(self)

    def showing(self, body: Nu | None = None, *, keep: bool = False) -> Nu:
        """This Ref on screen for as long as the term runs, and ``body`` with it.

        On enter the node comes up as declared (``init``), then ``body`` runs.
        A body that ends, or none at all, leaves the term parked, so the node
        stays up until whatever runs it is cancelled. On the way out, however
        it goes (a cancel, a raise), the node is erased, subtree and all. That
        is what a ``route`` branch is: entering the branch draws the page,
        leaving it takes the page away::

            nustd.ui.route(App.history, {"/": App.movies.showing(movies_work)})

        ``keep=True`` hides it on the way out instead and displays it on the
        way back, so the tree and its state (a typed filter, a scroll) stay
        in the browser between visits. The first enter still brings the node
        into being, since an init on a node that is there changes nothing.

        A leave that cannot reach the tab (it closed, which is what cancelled
        the term) has nothing left to clean, so a failed erase or hide is not
        an error.
        """
        import nu

        enter = (self.init() >> self.display()) if keep else self.init()
        leave = self.hide() if keep else self.erase()
        park = nu.ForeverDo(nu.Delay(3600.0))
        run = enter >> (park if body is None else body >> park)
        return nu.TryCatch(run, finally_=nu.TryCatch(leave, catch=lambda err: nu.Noop()))

    # --- declaration ---------------------------------------------------------

    @classmethod
    def slot(cls, **props: object) -> Self:
        return Slot(cls, props=props)  # type: ignore[return-value]
