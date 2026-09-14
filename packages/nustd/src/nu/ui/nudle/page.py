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
  add. That is the one-page shorthand -- serve.py auto-mounts a Page no
  Index declares, and refuses class handles for pages an Index does.
"""

from __future__ import annotations

from typing import ClassVar

from typing_extensions import Self

from nu.domains.shape import Shape, Slot
from nu.ui.core import Ref, Section, SectionRef
from nu.ui.core.base import _wire_type


# ``_wire_type`` lives in core now (the ref chain annotates itself with it);
# re-exported here because serve.py and the mount listing below import it.
__all__ = ["Index", "Page", "PageRef"]


def _build_fields(
    base_path: tuple[str, ...],
    shape_cls: type[Shape],
) -> list[dict[str, object]]:
    """Flatten a Shape's slots into mount field entries.

    Recurses into Section slots, emitting a nested `fields` list. Leaf
    Refs emit `{path, type, props?}`. Layout entries emit
    `{path, type, props?, fields}`. Paths are tuples built the same way
    the Ref chain builds them, so a mounted field and the Ref that drives
    it land on the same address.
    """
    out: list[dict[str, object]] = []
    for name, slot in shape_cls._slots.items():
        path = (*base_path, name)
        ref_cls = slot.ref_cls

        if issubclass(ref_cls, SectionRef):
            section_cls: type[Section] = slot.kwargs["section_cls"]
            entry: dict[str, object] = {
                "path": path,
                "type": _wire_type(section_cls),
            }
            if slot.props:
                entry["props"] = slot.props
            entry["fields"] = _build_fields(path, section_cls)
            out.append(entry)
            continue

        if not issubclass(ref_cls, Ref):
            continue
        entry = {"path": path, "type": _wire_type(ref_cls)}
        if slot.props:
            entry["props"] = slot.props
        out.append(entry)
    return out


class PageRef(SectionRef):
    """Substrate Ref backing a Page slot on an Index.

    A Page is a Section with a route, so navigating into it is plain
    ``SectionRef`` navigation (``App.home.panel.label``) and the page's
    segment is the Index slot name like any other segment. The route rides
    in the payload for the mount listing.
    """

    def __init__(
        self,
        address: object,
        *,
        section_cls: type[Page],
        route: str,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            section_cls=section_cls,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._payload["route"] = route


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

    # Optional human label used by the built-in sidebar. When None, the
    # sidebar falls back to the route slug (leading '/' stripped, or "home"
    # for the root route).
    nav_label: ClassVar[str | None] = None

    @classmethod
    def slot(cls, route: str, **props: object) -> Self:  # type: ignore[override]
        """Declare this Page on an Index at ``route``."""
        return Slot(cls._ref_cls, props=props, section_cls=cls, route=route)  # type: ignore[return-value]

    @classmethod
    def _mount_fields(cls) -> list[dict[str, object]]:
        """Flatten Page slots into mount field entries, rooted bare.

        Only the auto-mount path uses this: a Page no Index declares was
        never navigated to, so its fields start at its own slot names --
        the same addresses ``HomePage.panel.label`` resolves to.
        """
        return _build_fields((), cls)


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
    def _structural_fields(cls) -> list[dict[str, object]]:
        """Index-level slot list: structural Refs (title, nav, ...)."""
        out: list[dict[str, object]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if issubclass(ref_cls, PageRef) or not issubclass(ref_cls, Ref):
                continue
            entry: dict[str, object] = {"path": (name,), "type": _wire_type(ref_cls)}
            if slot.props:
                entry["props"] = slot.props
            out.append(entry)
        return out

    @classmethod
    def _pages_payload(cls) -> list[dict[str, object]]:
        """Per-page mount info: route, slot name, label, fields list.

        Fields are rooted at the page's slot name, which is the segment the
        Ref chain puts there too.
        """
        out: list[dict[str, object]] = []
        for name, slot in cls._page_slots():
            page_cls: type[Page] = slot.kwargs["section_cls"]
            route: str = slot.kwargs["route"]
            out.append(
                {
                    "route": route,
                    "name": name,
                    "label": page_cls.nav_label or route.lstrip("/") or "home",
                    "fields": _build_fields((name,), page_cls),
                }
            )
        return out

    @classmethod
    def _sidebar_enabled(cls) -> bool:
        """Built-in left sidebar is on when there is more than one page and
        the Index has not opted out via ``sidebar = False``.
        """
        return cls.sidebar and len(cls._page_slots()) > 1
