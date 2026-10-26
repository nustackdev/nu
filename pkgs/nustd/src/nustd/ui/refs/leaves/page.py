"""Page leaves -- the small furniture of a page: icons, spacers, page links, nav items.

Server-owned sinks like the content leaves: the server pushes props with
``write``, the browser only renders. A write is a partial merge of props, so
each setter sends just the keys it names. Every Ref here is a ``LeafRef``.

- ``IconRef``: one glyph by name, for feature lists and page headers.
- ``SpacerRef``: empty room that takes what a Row has left, so what follows
  sits at the end.
- ``PageLinkRef``: a link to a page drawn as the page: a row, a tile, or inline.
- ``NavItemRef``: one link in a sidebar or a top bar, active on its page.

Icon names are lucide's, in kebab case, from the kit's curated set: the
names listed on ``ButtonRef``, page furniture included. An unknown name
draws nothing and warns in the browser console.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from ..vocab import IconTone, Target
from ..vocab import set_href as _set_href
from .base import LeafRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, StrArg


__all__ = ["IconRef", "NavItemRef", "PageLinkRef", "SpacerRef"]


IconSize = Literal["xs", "sm", "md", "lg", "xl"]
PageLinkVariant = Literal["row", "tile", "inline"]


class IconRef(LeafRef):
    """One glyph by name.

    `size` runs 12, 14, 16, 20 and 24 px; `tone` "inherit" takes the color
    of the text around it. In a Line it is a run of the sentence, text sized
    on the baseline whatever `size` says. `framed` sets it in a soft square
    tinted by the tone, the leading mark of a feature or a page header.
    `label` is what a screen reader calls it; unset, it is decoration.
    """

    _wire_type = "IconRef"

    @classmethod
    def slot(
        cls,
        *,
        name: str = "",
        size: IconSize = "md",
        tone: IconTone = "inherit",
        framed: bool = False,
        label: str = "",
    ) -> Self:
        return super().slot(name=name, size=size, tone=tone, framed=bool(framed), label=label)

    def set(self, name: StrArg) -> Nu:
        return Write(self, Dict.of(name=name))

    def set_tone(self, name: IconTone | StrArg) -> Nu:
        return Write(self, Dict.of(tone=name))


class SpacerRef(LeafRef):
    """Empty room that takes what the line has left.

    In a Row the children after it sit at the end of the line; in a Column
    with a height of its own (a sidebar) it pushes what follows to the
    bottom. Two spacers split the room between them.
    """

    _wire_type = "SpacerRef"

    @classmethod
    def slot(cls) -> Self:
        return super().slot()


class PageLinkRef(LeafRef):
    """A link to a page, drawn as the page: mark, title, a line, a note.

    "row" is one line in a list of pages, "tile" a card in a grid of them,
    "inline" the page's mark and title alone on one line, a mention in prose
    or a Line; it draws no `description` and no `meta`, which it still
    carries for a switch back to the other two. `icon` is an icon name or
    any short text drawn as is, an emoji most often. `meta` trails: a date,
    a count, an owner. It is a real link, so a
    host that routes same-origin links routes it. The props are plain: what
    the page is called and how it looks are the caller's to fill in, from
    wherever it keeps its pages.
    """

    _wire_type = "PageLinkRef"

    @classmethod
    def slot(
        cls,
        *,
        href: str = "",
        title: str = "",
        icon: str = "",
        description: str = "",
        meta: str = "",
        variant: PageLinkVariant = "row",
        target: Target = "_self",
    ) -> Self:
        return super().slot(
            href=href,
            title=title,
            icon=icon,
            description=description,
            meta=meta,
            variant=variant,
            target=target,
        )

    def set(
        self,
        href: StrArg = UNSET,
        title: StrArg = UNSET,
        icon: StrArg = UNSET,
        description: StrArg = UNSET,
        meta: StrArg = UNSET,
        target: Target | StrArg = UNSET,
    ) -> Nu:
        """Point it at a page; only the fields passed change."""
        fields = {
            "href": href,
            "title": title,
            "icon": icon,
            "description": description,
            "meta": meta,
            "target": target,
        }
        return Write(self, Dict.of(**{k: v for k, v in fields.items() if v is not UNSET}))

    def set_meta(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(meta=text))

    def set_variant(self, name: PageLinkVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point it at another page; ``target`` too when given, else it keeps its own."""
        return _set_href(self, url, target)


class NavItemRef(LeafRef):
    """One link in a sidebar or a top bar, active on its own page.

    `active` None (the default) follows the tab: active while its path is
    `href`'s or under it ("/docs" on "/docs/intro"), only the path itself
    when `exact`. "/" matches only itself. True or False pins it. `meta`
    trails the label: a count, a shortcut. In a vertical NavList (or any
    Column) it is a full width row; in a horizontal one, its own width.
    `target` "_blank" opens it in a new tab, like every kit link.
    """

    _wire_type = "NavItemRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        href: str = "",
        icon: str = "",
        meta: str = "",
        active: bool | None = None,
        exact: bool = False,
        target: Target = "_self",
    ) -> Self:
        return super().slot(
            label=label,
            href=href,
            icon=icon,
            meta=meta,
            active=None if active is None else bool(active),
            exact=bool(exact),
            target=target,
        )

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point it at another page; ``target`` too when given, else it keeps its own."""
        return _set_href(self, url, target)

    def set_active(self, flag: BoolArg | None) -> Nu:
        """Pin it active or not; None goes back to following the tab."""
        return Write(self, Dict.of(active=flag))

    def set_meta(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(meta=text))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))
