"""Top-level Shape kinds.

- `Index`: the browser entrypoint. One per app. Carries structural Refs
  (document title, navigation, ...) and a `pages` map.
- `Page`: a sub-shape that lives inside an Index's `pages` map. Display
  Refs and Section slots only.
- `Pages`: declarative class-attribute holder mapping URI -> Page subclass.

Wire-path rule (see refs/base.py NudleRef.aresolve):
- Refs whose root shape is an `Index` resolve to their slot name alone
  ("title", "nav"). These are Index-level structural slots.
- Refs whose root shape is a `Page` resolve to "<PageShapeName>.<slot>"
  ("HomePage.count"). Each page is namespaced so all pages can be mounted
  at once without path collisions.
- Refs whose root shape is a `Section` resolve via the Section's
  registered mount point on a Page (see `Section._nudle_mount`).
"""

from __future__ import annotations

from typing import ClassVar

from nu.shapes.shape import Shape

from .refs.base import NudleRef
from .refs.section import Section, SectionRef


__all__ = ["Index", "Page", "Pages"]


def _wire_type(ref_or_section_cls: type) -> str:
    """Canonical (registered) class name for a Ref or Section.

    Walks the MRO to find the closest ancestor defined inside the
    `nudle.refs` package (excluding the abstract `base` module). User
    subclasses defined outside the package inherit the wire type of
    their nearest packaged ancestor so the browser registry resolves
    them.
    """
    for base in ref_or_section_cls.__mro__:
        mod = getattr(base, "__module__", "")
        if not mod.startswith("nudle.refs."):
            continue
        if mod == "nudle.refs.base":
            continue
        return base.__name__
    return ref_or_section_cls.__name__


def _register_section_mounts(
    page_cls: type[Page],
    section_cls: type[Section],
    path_segments: tuple[str, ...],
) -> None:
    """Walk a Section's slots; register mount points for nested Sections.

    Raises if the same Section subclass is mounted twice anywhere in the
    Index tree (constraint: one Section, one mount point).
    """
    existing = section_cls.__dict__.get("_nudle_mount")
    if existing is not None and existing != (page_cls, path_segments):
        raise RuntimeError(
            f"Section {section_cls.__name__} is mounted at "
            f"{existing[0].__name__}.{'.'.join(existing[1])} and cannot be "
            f"reused at {page_cls.__name__}.{'.'.join(path_segments)}. "
            "Each Section subclass must be mounted at exactly one Slot.",
        )
    section_cls._nudle_mount = (page_cls, path_segments)

    for name, slot in section_cls._slots.items():
        if issubclass(slot.ref_cls, SectionRef):
            child_section_cls = slot.kwargs["section_cls"]
            _register_section_mounts(
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
            props = section_cls.mount_props()
            if props:
                entry["props"] = props
            entry["fields"] = _build_fields(path, section_cls)
            out.append(entry)
            continue

        if not issubclass(ref_cls, NudleRef):
            continue
        entry = {"path": path, "type": _wire_type(ref_cls)}
        props = ref_cls.mount_props()
        if props:
            entry["props"] = props
        out.append(entry)
    return out


class Page(Shape):
    """Sub-shape that lives inside an Index's `pages` map."""

    _is_nudle_page: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Register mount points for every Section slot on this Page.
        for name, slot in cls._slots.items():
            if issubclass(slot.ref_cls, SectionRef):
                section_cls = slot.kwargs["section_cls"]
                _register_section_mounts(cls, section_cls, (name,))

    @classmethod
    def mount_fields(cls) -> list[dict[str, object]]:
        """Flatten Page slots into mount field entries.

        Paths are prefixed with the Page class name so wire paths are
        unique across all pages in an Index. Section slots emit nested
        `fields` lists recursively.
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
    `pages` attribute of type `Pages` mapping URIs to Page subclasses.
    """

    _is_nudle_index: ClassVar[bool] = True

    pages: ClassVar[Pages] = Pages({})

    @classmethod
    def structural_fields(cls) -> list[dict[str, object]]:
        """Index-level slot list: structural Refs (title, nav, ...)."""
        out: list[dict[str, object]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if not issubclass(ref_cls, NudleRef):
                continue
            entry: dict[str, object] = {"path": name, "type": _wire_type(ref_cls)}
            props = ref_cls.mount_props()
            if props:
                entry["props"] = props
            out.append(entry)
        return out

    @classmethod
    def pages_payload(cls) -> list[dict[str, object]]:
        """Per-page mount info: route, shape name, fields list."""
        out: list[dict[str, object]] = []
        for route, page_cls in cls.pages.routes.items():
            out.append(
                {
                    "route": route,
                    "name": page_cls.__name__,
                    "fields": page_cls.mount_fields(),
                }
            )
        return out
