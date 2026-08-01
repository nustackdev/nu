"""Top-level Shape kinds for nudle.

- ``Index``: the browser entrypoint. One per app. Carries structural Refs
  (document title, navigation, ...) and a ``pages`` map.
- ``Page``: a sub-shape that lives inside an Index's ``pages`` map. Display
  Refs and Section slots only.
- ``Pages``: declarative class-attribute holder mapping URI -> Page subclass.

Wire-path rule (via ``Ref._aresolve_address`` + ``_wire_prefix`` hook):
- Refs rooted on an ``Index`` resolve to their slot name alone ("title",
  "nav") -- Index carries no ``_wire_prefix`` so segments join bare.
- Refs rooted on a ``Page`` resolve to "<PageShapeName>.<slot>"; ``Page``
  defines ``_wire_prefix`` returning ``[cls.__name__]``.
- Refs rooted on a ``Section`` mounted under a Page resolve via the
  ``_wire_prefix`` classmethod stamped on the section subclass here
  (``[page_cls.__name__, *slot_path]``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import Shape
from nu.ui.core import Ref, SectionRef


if TYPE_CHECKING:
    from nu.ui.core.section import Section


__all__ = ["Index", "Page", "Pages"]


_REFS_PKG = "nu.ui.refs."
_REFS_BASE = f"{_REFS_PKG}base"


def _wire_type(ref_or_section_cls: type) -> str:
    """Canonical (registered) class name for a Ref or Section.

    Walks the MRO to find the closest ancestor defined inside the
    ``nu.ui.refs`` package (excluding the abstract ``base`` module). User
    subclasses defined outside the package inherit the wire type of their
    nearest packaged ancestor so the browser registry resolves them.
    """
    for base in ref_or_section_cls.__mro__:
        mod = getattr(base, "__module__", "")
        if not mod.startswith(_REFS_PKG):
            continue
        if mod == _REFS_BASE:
            continue
        return base.__name__
    return ref_or_section_cls.__name__


def _stamp_section_mount(
    page_cls: type[Page],
    section_cls: type[Section],
    path_segments: tuple[str, ...],
) -> None:
    """Attach nudle's wire prefix to a Section subclass.

    Stamps two attributes on ``section_cls``:
      - ``_wire_mount_key``: identity tuple (page, path) for dedup detection.
      - ``_wire_prefix``: classmethod ``Ref._aresolve_address`` reads to
        build the section-rooted address.

    Raises if the same Section subclass is mounted twice anywhere in the
    Index tree (constraint: one Section, one mount point).
    """
    existing = section_cls.__dict__.get("_wire_mount_key")
    if existing is not None and existing != (page_cls, path_segments):
        raise RuntimeError(
            f"Section {section_cls.__name__} is mounted at "
            f"{existing[0].__name__}.{'.'.join(existing[1])} and cannot be "
            f"reused at {page_cls.__name__}.{'.'.join(path_segments)}. "
            "Each Section subclass must be mounted at exactly one Slot.",
        )
    section_cls._wire_mount_key = (page_cls, path_segments)

    def _prefix(
        cls: type[Section], _p: type[Page] = page_cls, _s: tuple[str, ...] = path_segments
    ) -> list[str]:
        return [_p.__name__, *_s]

    section_cls._wire_prefix = classmethod(_prefix)

    for name, slot in section_cls._slots.items():
        if issubclass(slot.ref_cls, SectionRef):
            child_section_cls = slot.kwargs["section_cls"]
            _stamp_section_mount(
                page_cls,
                child_section_cls,
                (*path_segments, name),
            )


def _build_fields(
    base_path: str,
    shape_cls: type[Shape],
) -> list[dict[str, object]]:
    """Flatten a Shape's slots into mount field entries.

    Recurses into Section slots, emitting a nested `fields` list. Leaf
    Refs emit `{path, type, props?}`. Layout entries emit
    `{path, type, props?, fields}`.
    """
    out: list[dict[str, object]] = []
    for name, slot in shape_cls._slots.items():
        path = f"{base_path}.{name}"
        ref_cls = slot.ref_cls

        if issubclass(ref_cls, SectionRef):
            section_cls: type[Section] = slot.kwargs["section_cls"]
            entry: dict[str, object] = {
                "path": path,
                "type": _wire_type(section_cls),
            }
            props = {**section_cls._mount_props(), **slot.props}
            if props:
                entry["props"] = props
            entry["fields"] = _build_fields(path, section_cls)
            out.append(entry)
            continue

        if not issubclass(ref_cls, Ref):
            continue
        entry = {"path": path, "type": _wire_type(ref_cls)}
        props = {**ref_cls._mount_props(), **slot.props}
        if props:
            entry["props"] = props
        out.append(entry)
    return out


class Page(Shape):
    """Sub-shape that lives inside an Index's ``pages`` map."""

    # Optional human label used by the built-in sidebar. When None, the
    # sidebar falls back to the route slug (leading '/' stripped, or "home"
    # for the root route).
    nav_label: ClassVar[str | None] = None

    @classmethod
    def _wire_prefix(cls) -> list[str]:
        """Wire prefix for Refs rooted on this Page: ``[<PageShapeName>]``."""
        return [cls.__name__]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Register mount points for every Section slot on this Page.
        for name, slot in cls._slots.items():
            if issubclass(slot.ref_cls, SectionRef):
                section_cls = slot.kwargs["section_cls"]
                _stamp_section_mount(cls, section_cls, (name,))

    @classmethod
    def _mount_fields(cls) -> list[dict[str, object]]:
        """Flatten Page slots into mount field entries.

        Paths are prefixed with the Page class name so wire paths are
        unique across all pages in an Index. Section slots emit nested
        ``fields`` lists recursively.
        """
        return _build_fields(cls.__name__, cls)


class Pages:
    """Declarative map of URI -> Page subclass.

    Class-attribute holder, not a Slot:

        class App(nudle.Index):
            ...
            pages = nudle.Pages({"/": HomePage, "/feed": FeedPage})
    """

    __slots__ = ("routes",)

    def __init__(self, routes: dict[str, type[Page]]) -> None:
        for route, page_cls in routes.items():
            if not isinstance(route, str):
                raise TypeError(f"Pages route must be str, got {type(route).__name__}")
            if not (isinstance(page_cls, type) and issubclass(page_cls, Page)):
                raise TypeError(
                    f"Pages value for {route!r} must be a Page subclass, got {page_cls!r}",
                )
        self.routes: dict[str, type[Page]] = dict(routes)


class Index(Shape):
    """Browser entrypoint. One per app.

    Class body declares structural Refs as Slots (title, nav, ...) and a
    ``pages`` attribute of type ``Pages`` mapping URIs to Page subclasses.

    Refs rooted on an Index resolve to their slot name alone -- no
    ``_wire_prefix`` here, so ``Ref._aresolve_address`` joins segments bare.
    """

    pages: ClassVar[Pages] = Pages({})

    # Opt-out for the built-in left sidebar. Off automatically when there
    # is only one page; setting False suppresses it even with multiple pages.
    sidebar: ClassVar[bool] = True

    @classmethod
    def _structural_fields(cls) -> list[dict[str, object]]:
        """Index-level slot list: structural Refs (title, nav, ...)."""
        out: list[dict[str, object]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if not issubclass(ref_cls, Ref):
                continue
            entry: dict[str, object] = {"path": name, "type": _wire_type(ref_cls)}
            props = {**ref_cls._mount_props(), **slot.props}
            if props:
                entry["props"] = props
            out.append(entry)
        return out

    @classmethod
    def _pages_payload(cls) -> list[dict[str, object]]:
        """Per-page mount info: route, shape name, label, fields list."""
        out: list[dict[str, object]] = []
        for route, page_cls in cls.pages.routes.items():
            out.append(
                {
                    "route": route,
                    "name": page_cls.__name__,
                    "label": page_cls.nav_label or route.lstrip("/") or "home",
                    "fields": page_cls._mount_fields(),
                }
            )
        return out

    @classmethod
    def _sidebar_enabled(cls) -> bool:
        """Built-in left sidebar is on when there is more than one page and
        the Index has not opted out via ``sidebar = False``.
        """
        return cls.sidebar and len(cls.pages.routes) > 1
