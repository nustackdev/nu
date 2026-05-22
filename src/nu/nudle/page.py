"""Top-level Shape kinds.

- `Index`: the browser entrypoint. One per app. Carries structural Refs
  (document title, navigation, ...) and a `pages` map.
- `Page`: a sub-shape that lives inside an Index's `pages` map. Display
  Refs only.
- `Pages`: declarative class-attribute holder mapping URI -> Page subclass.

Wire-path rule (see refs/base.py NudleRef.aresolve):
- Refs whose root shape is an `Index` resolve to their slot name alone
  ("title", "nav"). These are Index-level structural slots.
- Refs whose root shape is a `Page` resolve to "<PageShapeName>.<slot>"
  ("HomePage.count"). Each page is namespaced so all pages can be mounted
  at once without path collisions.

"""

from __future__ import annotations

from typing import ClassVar

from nu.shapes.shape import Shape

from .refs.base import NudleRef


__all__ = ["Index", "Page", "Pages"]


class Page(Shape):
    """Sub-shape that lives inside an Index's `pages` map."""

    _is_nudle_page: ClassVar[bool] = True

    @classmethod
    def mount_fields(cls) -> list[dict[str, object]]:
        """Flatten Page slots into `{path, type, props?}` dicts.

        Paths are prefixed with the Page class name so wire paths are
        unique across all pages in an Index. `props` is included only when
        the Ref class exposes non-empty class-level defaults via
        `mount_props()`.
        """
        out: list[dict[str, object]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if not issubclass(ref_cls, NudleRef):
                continue
            entry: dict[str, object] = {
                "path": f"{cls.__name__}.{name}",
                "type": ref_cls.__name__,
            }
            props = ref_cls.mount_props()
            if props:
                entry["props"] = props
            out.append(entry)
        return out


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
            entry: dict[str, object] = {"path": name, "type": ref_cls.__name__}
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
