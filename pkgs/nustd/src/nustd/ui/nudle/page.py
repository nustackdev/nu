"""Top-level Shape kinds for nudle, and the term that boots one.

- ``Index``: the browser entrypoint. One per app. Carries structural Refs
  (document title, navigation, ...) and one slot per Page.
- ``Page``: a Section an Index mounts at a route. Display Refs and Section
  slots only.
- ``Boot``: the init batch for either of them, as a Nu term.

Wire-path rule: the address is the Ref chain, nothing else (see
``Ref._aresolve_address``). A segment is in a path because something
navigated through it, never because a class named itself.

- Refs rooted on an ``Index`` resolve from the slot down: ``("title",)``
  for a structural Ref, ``("home", "panel", "label")`` for one inside a
  page. Two pages can both declare a ``panel`` and land at different
  addresses.
- Taken off the class (``HomePage.panel.label``) a Page resolves bare, like
  any Section. That is the one-page shorthand, and ``Page.boot()`` emits
  those bare addresses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nu.domains.shape import Shape, Slot
from nu.engine.structure import Declared
from nu.lang import Command
from nustd.ui.core import Section, SectionRef
from nustd.ui.core.chains import Chain, boot_chains
from nustd.ui.core.protocol import OP_INIT, OP_REMOVE, OP_WRITE, Frame
from nustd.ui.core.session import Session


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Boot", "Chain", "Index", "Page", "PageRef"]


class Boot(Command):
    """Seed one browser's tree: clear it, name it, then one ``init`` per slot.

    Runs with one connection's Session bound, once per live connection and
    never for anybody else's.

    Three frames, in order. The clearing ``remove`` goes first because a
    reconnect gets a fresh session with none of the old one's dynamic nodes,
    which would otherwise sit there forever. Then the root write, carrying
    what the shell itself needs -- the app name and whether the built-in
    sidebar is on. Then the slots, in declaration order, which is render
    order.

    ``_mutates`` is declared and empty: the browser's tree root is not
    something any Nu Ref names, and a mutation with no address is a local
    change rather than an effect.

    Args:
        shape_cls: the Index, or the lone Page, whose slots seed the tree.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, shape_cls: type[Shape]) -> None:
        super().__init__()
        self._payload["shape_cls"] = shape_cls

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        # Name, chains and sidebar are pure class statics, so they resolve once
        # per compile rather than per run, and the payload stays the class
        # alone, which is hashable across a tree rewrite.
        shape_cls = self._payload["shape_cls"]
        name = shape_cls.__name__
        chains = shape_cls._boot_chains()
        sidebar = shape_cls._sidebar_enabled() if issubclass(shape_cls, Index) else False

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            # Down this connection's socket and no other: the clearing remove
            # wipes the tab that is booting, never a sibling tab's tree.
            await session.send(Frame(OP_REMOVE))
            await session.send(Frame(OP_WRITE, payload={"name": name, "sidebar": sidebar}))
            for chain in chains:
                await session.send(
                    Frame(OP_INIT, ref=[seg for seg, _, _ in chain], chain=chain),
                )

        return athunk


class PageRef(SectionRef):
    """Substrate Ref backing a Page slot on an Index.

    A Page is a Section with a route, so navigating into it is plain
    ``SectionRef`` navigation (``App.home.panel.label``). The class exists so
    ``_page_slots`` can tell a page slot from a plain section slot.
    """

    _wire_type: ClassVar[str] = "Page"


class Page(Section):
    """Section an Index mounts at a route.

    A Page holds no mount point of its own. It gets one by being declared
    as a slot on an Index, which is where its address segment comes from::

        class App(nudle.Index):
            home = HomePage.slot("/")
            feed = FeedPage.slot("/feed")

        App.home.panel.label.set("hi")   # ("home", "panel", "label")
    """

    _ref_cls: ClassVar[type[SectionRef]] = PageRef

    # Every Page subclass draws as the browser's "Page" node, whatever the
    # user calls it. The class name never reaches the wire.
    _wire_type: ClassVar[str] = "Page"

    # Optional human label used by the built-in sidebar. When None, the
    # sidebar falls back to the route slug (leading '/' stripped, or "home"
    # for the root route).
    nav_label: ClassVar[str | None] = None

    @classmethod
    def slot(cls, route: str, **props: object) -> Self:  # type: ignore[override]
        """Declare this Page on an Index at ``route``.

        ``route`` and ``label`` go in as declared props, which is how they
        reach the browser's router and sidebar: the chain carries them onto
        the page node.
        """
        declared: dict[str, object] = {
            "route": route,
            "label": cls.nav_label or route.lstrip("/") or "home",
            **props,
        }
        return Slot(cls._ref_cls, props=declared, section_cls=cls)  # type: ignore[return-value]

    @classmethod
    def boot(cls) -> Boot:
        """The init batch for this Page, as a term to put at the head of an arm.

        ``HomePage.boot() >> program`` is the whole idiom: the browser shows
        "waiting for the tree..." until the inits land, so this runs before
        anything writes.
        """
        return Boot(cls)

    @classmethod
    def _boot_chains(cls) -> list[Chain]:
        """This Page's slots, rooted bare.

        The one-page shorthand: a Page no Index declares was never navigated
        to, so its slots start at their own names.
        """
        return boot_chains((), cls)


class Index(Shape):
    """Browser entrypoint. One per app.

    Class body declares structural Refs as Slots (title, nav, ...) and one
    Page slot per route::

        class App(nudle.Index):
            title = nudle.TitleRef.slot()
            home = HomePage.slot("/")
            feed = FeedPage.slot("/feed")

    Refs rooted on an Index resolve from their slot down, so a structural
    Ref is one segment and a page's Refs carry the page slot in front.
    """

    # Opt-out for the built-in left sidebar. Off automatically when there
    # is only one page; setting False suppresses it even with multiple pages.
    sidebar: ClassVar[bool] = True

    @classmethod
    def boot(cls) -> Boot:
        """The init batch for this Index, as a term to put at the head of an arm.

        ``App.boot() >> program`` is the whole idiom: the browser shows
        "waiting for the tree..." until the inits land, so this runs before
        anything writes.
        """
        return Boot(cls)

    @classmethod
    def _page_slots(cls) -> list[tuple[str, Slot]]:
        """``(slot_name, slot)`` for every Page declared on this Index."""
        return [
            (name, slot) for name, slot in cls._slots.items() if issubclass(slot.ref_cls, PageRef)
        ]

    @classmethod
    def _page_slot_name(cls, page_cls: type[Page]) -> str | None:
        """Slot ``page_cls`` is declared at here, or None if it isn't."""
        for name, slot in cls._page_slots():
            if slot.kwargs["section_cls"] is page_cls:
                return name
        return None

    @classmethod
    def _boot_chains(cls) -> list[Chain]:
        """Everything this Index declares, as chains, in declaration order.

        Structural Refs and page subtrees come out of the same walk: a page
        slot is a Section slot that happens to carry a route.
        """
        return boot_chains((), cls)

    @classmethod
    def _sidebar_enabled(cls) -> bool:
        """On when there is more than one page and the Index has not opted out."""
        return cls.sidebar and len(cls._page_slots()) > 1
