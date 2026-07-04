"""Section -- Shape-based layout primitive.

A Section is a Shape subclass that carries layout chrome as class attrs
(gap, align, padding, ...) AND child slots in its body. Subclasses like
`Row`, `Column`, `Container` (in `nudle.refs.*`) are the user-facing
layout primitives.

Sections nest. `HomePage.toolbar.text` is the wire path of a TextRef
declared on a `Toolbar(Row)` Section that is mounted at
`HomePage.toolbar`.

A Section subclass is mounted at exactly one Slot in the entire Index
tree. Reuse raises at Page class creation time. The Page (or parent
Section) registers `_nudle_mount = (PageClass, ("toolbar", ...))` on the
Section class; `NudleRef.aresolve_address` uses this registry to build
the full wire path from a server-side handle like `Toolbar.text`.

See `projects/nu/stack/nudle/protocol.md` for the recursive `fields`
mount-payload extension.
"""

from __future__ import annotations

from typing import ClassVar, Self

from nu import Shape
from nu.domains.shape import Slot

from .base import NudleRef


__all__ = ["Section", "SectionRef"]


class SectionRef(NudleRef):
    """Internal Ref backing a Section slot.

    Instances are created by `Section.slot()` and exposed at Page or
    parent-Section class level (e.g. `HomePage.toolbar`). The instance
    carries `section_cls`; attribute access on it (e.g. `.text`) returns
    a child Ref whose `parent` is this SectionRef.
    """

    def __init__(
        self,
        address: object,
        *,
        section_cls: type[Section],
        parent_ref: NudleRef | None = None,
        owner_shape: type[Section] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self.payload["section_cls"] = section_cls

    @property
    def section_cls(self) -> type[Section]:
        return self._section_cls  # type: ignore[return-value]

    def __getattr__(self, name: str) -> object:
        # Only called when normal attribute lookup fails. Map to a child
        # slot on the bound Section class. Read payload straight off __dict__ so
        # this never recurses back through __getattr__.
        payload = self.__dict__.get("payload") or {}
        section_cls = payload.get("section_cls")
        if section_cls is None:
            raise AttributeError(name)
        slots = getattr(section_cls, "_slots", {})
        if name in slots:
            slot = slots[name]
            return slot.create_ref(owner_shape=section_cls, parent_ref=self)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
            f" (section '{section_cls.__name__}' has no slot '{name}')"
        )


class Section(Shape):
    """Base for Shape-based layout primitives.

    Subclass `Row`, `Column`, `Container` (defined in `nudle.refs`). User
    code subclasses those to pin chrome defaults and declare child slots:

        class Toolbar(nudle.Row):
            gap = 3
            text = nudle.TextRef.slot()
            btn = nudle.ButtonRef.slot()
    """

    _is_nudle_section: ClassVar[bool] = True
    # Filled in by the enclosing Page (or parent Section) at class
    # creation time. Tuple of slot-path segments from the owning Page
    # down to (but not including) this section.
    # Example: HomePage.toolbar -> ("toolbar",)
    # Example: HomePage.panel.toolbar -> ("panel", "toolbar")
    _nudle_mount: ClassVar[tuple[type, tuple[str, ...]] | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        """Class-level layout chrome shipped in the mount field entry."""
        return {}

    @classmethod
    def slot(cls) -> Self:
        return Slot(SectionRef, section_cls=cls)  # type: ignore[return-value]
