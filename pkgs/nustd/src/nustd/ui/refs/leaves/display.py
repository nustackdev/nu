"""Display leaves -- small status and identity marks.

STUBS, wired end to end so the display unit only fills them in: each class
has its wire type and a first ``slot()``, and the kit node draws the smallest
honest thing with its primitive. No ``set()`` yet; the unit adds the setters
with the full props.

- ``AvatarRef``: an image or initials for a person or thing.
- ``BreadcrumbRef``: the trail to here; the crumbs are data, not children.
- ``SkeletonRef``: a loading placeholder for a cell that fetches.
- ``SpinnerRef``: busy with no known progress (``ProgressRef`` covers known).
- ``StatusPillRef``: icon + label status that reads without color.
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import Self

from .base import LeafRef


__all__ = ["AvatarRef", "BreadcrumbRef", "SkeletonRef", "SpinnerRef", "StatusPillRef"]


class AvatarRef(LeafRef):
    """Image when ``src`` loads, initials from ``name`` when it does not."""

    _wire_type = "AvatarRef"

    @classmethod
    def slot(cls, *, src: str = "", name: str = "") -> Self:
        return super().slot(src=src, name=name)


class BreadcrumbRef(LeafRef):
    """Trail of crumbs, each ``{label, href}``; the last is the current page."""

    _wire_type = "BreadcrumbRef"

    @classmethod
    def slot(cls, *, items: list[dict[str, str]] | None = None) -> Self:
        return super().slot(items=list(items or []))


class SkeletonRef(LeafRef):
    """Pulsing placeholder lines while content loads."""

    _wire_type = "SkeletonRef"

    @classmethod
    def slot(cls, *, lines: int = 1) -> Self:
        return super().slot(lines=int(lines))


class SpinnerRef(LeafRef):
    """Busy indicator; ``label`` names it for screen readers."""

    _wire_type = "SpinnerRef"

    @classmethod
    def slot(cls, *, label: str = "") -> Self:
        return super().slot(label=label)


Tone = Literal["neutral", "info", "ok", "warn", "danger"]


class StatusPillRef(LeafRef):
    """Status as icon + label, so it reads without color."""

    _wire_type = "StatusPillRef"

    @classmethod
    def slot(cls, *, tone: Tone = "neutral", label: str = "") -> Self:
        return super().slot(tone=tone, label=label)
