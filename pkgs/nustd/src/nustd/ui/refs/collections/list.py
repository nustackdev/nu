"""``ListRef`` -- a bulleted or numbered list whose items are any children.

A container. Plain string items render first, from the ``items`` prop; then
every child is one more item after them. Positions (``lst[0]``) draw in
index order; names (``lst["k"]``) in the order they were first written.
There is no item Ref: any child is an item, so a Badge, a Link or a whole
Row can each be one.

The string half is for short text lists: ``set(items)`` replaces the strings
whole, ``append`` adds one to the end, ``clear`` empties them, and none of
the three touches the children. That makes it the one container with a
``set()`` that is not chrome.

The child half is a keyed, ordered collection, the same as a Row's or a
Column's: ``insert``, ``move``, ``remove``, ``truncate``, ``keep`` and
``set_order`` (see ``order``). They reorder children only; the string items
always draw first.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self, Unpack

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Append, Write

from .base import DictCollectionRef
from .layout import SIZE, SPACE, SpaceLayout
from .order import Ordered


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import IntArg, ListArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = ["ListRef"]


ListVariant = Literal["bullet", "number"]


class ListLayout(SpaceLayout, total=False):
    """A List's layout: size, space, and a hairline between items."""

    divided: bool


class ListRef(Ordered, DictCollectionRef):
    """A bulleted or numbered list: string items first, then each child.

    One string per item, drawn as given. `set` replaces the strings whole,
    `append` adds one to the end. `start` is the first number of a numbered
    list, and children carry the numbering on after the strings. Composes
    the kit List primitive, which draws a list the way a markdown list
    renders in prose. Layers (``layout``): size, ``padding`` (4px top and
    bottom unless set), ``gap`` between items, ``divided``.
    """

    _wire_type = "List"
    _layout: ClassVar[frozenset[str]] = SIZE | SPACE | {"divided"}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        items: list[str] | None = None,
        variant: ListVariant = "bullet",
        start: int = 1,
        **layout: Unpack[ListLayout],
    ) -> Self:
        return super().slot(
            item,
            items=list(items or []),
            variant=variant,
            start=int(start),
            **cls._laid_out(layout),
        )

    def set(
        self,
        items: ListArg[str],
        variant: ListVariant | StrArg = UNSET,
        start: IntArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"items": items}
        if variant is not UNSET:
            payload["variant"] = variant
        if start is not UNSET:
            payload["start"] = start
        return Write(self, Dict.of(**payload))

    def set_variant(self, name: ListVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def append(self, item: StrArg) -> Nu:
        return Append(self, item)

    def clear(self) -> Nu:
        return Write(self, Dict.of(items=[]))
