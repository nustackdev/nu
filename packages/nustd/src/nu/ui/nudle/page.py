"""Top-level Shape kinds for nudle.

- ``Index``: the browser entrypoint. One per app. Carries structural Refs
  (document title, navigation, ...) and one slot per Page.
- ``Page``: a Section an Index mounts at a route. Display Refs and Section
  slots only.

Wire-path rule: the address is the Ref chain, nothing else (see
``Ref._aresolve_address``). A segment is in a path because something
navigated through it, never because a class named itself.

- Refs rooted on an ``Index`` resolve from the slot down: ``("title",)``
  for a structural Ref, ``("home", "panel", "label")`` for one inside a
  page. The page's segment is the Index slot it was reached through, so
  two pages can both declare a ``panel`` and land at different addresses.
- Taken off the class (``HomePage.panel.label``) a Page resolves bare,
  exactly like a Section: no slot was navigated, so there is no segment to
  add. That is the one-page shorthand -- serve.py boots a Page no
  Index declares, and refuses class handles for pages an Index does.
"""

from __future__ import annotations

from typing import ClassVar

from typing_extensions import Self

from nu.domains.shape import Shape, Slot
from nu.ui.core import Ref, Section, SectionRef
from nu.ui.core.base import _wire_type


# ``_wire_type`` lives in core now (the ref chain annotates itself with it);
# re-exported here because serve.py imports it for the shape-less fallback.
__all__ = ["Chain", "Index", "Page", "PageRef"]


Chain = tuple[tuple[str, str, dict[str, object]], ...]


def _boot_chains(base: Chain, shape_cls: type[Shape]) -> list[Chain]:
    """Every slot under ``shape_cls`` as a chain, root-first, in order.

    One chain per declared slot, the same shape ``Ref._aresolve_chain``
    builds at write time -- ``(segment, type, props)`` per level. Shipped
    as ``init`` frames at boot so a slot is on screen before anything
    writes to it, and dropped straight into the browser's tree by the same
    autovivify walk a write takes.

    Depth-first in declaration order, so the browser's per-node insertion
    order is the order the class body reads.
    """
    out: list[Chain] = []
    for name, slot in shape_cls._slots.items():
        ref_cls = slot.ref_cls
        if not issubclass(ref_cls, Ref):
            continue
        if issubclass(ref_cls, SectionRef):
            section_cls: type[Section] = slot.kwargs["section_cls"]
            chain = (*base, (name, _wire_type(section_cls), dict(slot.props)))
            out.append(chain)
            out.extend(_boot_chains(chain, section_cls))
            continue
        out.append((*base, (name, _wire_type(ref_cls), dict(slot.props))))
    return out


class PageRef(SectionRef):
    """Substrate Ref backing a Page slot on an Index.

    A Page is a Section with a route, so navigating into it is plain
    ``SectionRef`` navigation (``App.home.panel.label``) and the page's
    segment is the Index slot name like any other segment. Nothing else is
    needed here: the route is a declared prop, so it rides the chain onto
    the page node and the browser's router reads it off the tree like any
    other prop. The class exists so ``_page_slots`` can tell a page slot
    from a plain section slot.
    """


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
    _wire_type_override: ClassVar[str] = "Page"

    # Optional human label used by the built-in sidebar. When None, the
    # sidebar falls back to the route slug (leading '/' stripped, or "home"
    # for the root route).
    nav_label: ClassVar[str | None] = None

    @classmethod
    def slot(cls, route: str, **props: object) -> Self:  # type: ignore[override]
        """Declare this Page on an Index at ``route``.

        ``route`` and ``label`` go in as declared props, which is how they
        reach the browser: the chain carries them onto the page node and
        the router and sidebar read them there.
        """
        declared: dict[str, object] = {
            "route": route,
            "label": cls.nav_label or route.lstrip("/") or "home",
            **props,
        }
        return Slot(cls._ref_cls, props=declared, section_cls=cls)  # type: ignore[return-value]

    @classmethod
    def _boot_chains(cls) -> list[Chain]:
        """This Page's slots, rooted bare.

        Only the auto-mount path uses this: a Page no Index declares was
        never navigated to, so its slots start at their own names -- the
        same addresses ``HomePage.panel.label`` resolves to.
        """
        return _boot_chains((), cls)


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
        slot is a Section slot that happens to carry a route, so its chain
        starts at the Index slot name, which is the segment the Ref chain
        puts there too.
        """
        return _boot_chains((), cls)

    @classmethod
    def _sidebar_enabled(cls) -> bool:
        """Built-in left sidebar is on when there is more than one page and
        the Index has not opted out via ``sidebar = False``.
        """
        return cls.sidebar and len(cls._page_slots()) > 1
