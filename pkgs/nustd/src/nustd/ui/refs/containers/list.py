"""``ListRef`` -- a bulleted or numbered list whose items are any nodes.

A container. Plain string items render first, from the ``items`` prop, the
way the list always drew; then every child node is one more item after
them. Indexed children (``list[0]``, from an item template) draw in index
order; named ones in the order they were first written. There is no item Ref: any child is
an item, so a Badge, a Link or a whole Row can each be one.

The string half stays for compatibility and because short text lists are
common: ``set(items)`` replaces the strings whole, ``append`` adds one to
the end, ``clear`` empties them, and none of the three touches the child
nodes. That makes it the one container with a ``set()`` that is not chrome.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Append, Write

from .base import ListContainerRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import IntArg, ListArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = ["ListRef"]


ListVariant = Literal["bullet", "number"]


class ListRef(ListContainerRef):
    """A bulleted or numbered list: string items first, then each child node.

    One string per item, drawn as given. `set` replaces the strings whole,
    `append` adds one to the end. `start` is the first number of a numbered
    list, and child nodes carry the numbering on after the strings. Composes
    the kit List primitive, which draws a list the way a markdown list
    renders in prose.

    Wire type stays "ListRef" so a bundle from before lists took children
    still draws the strings.
    """

    _wire_type = "ListRef"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        items: list[str] | None = None,
        variant: ListVariant = "bullet",
        start: int = 1,
    ) -> Self:
        return super().slot(item, items=list(items or []), variant=variant, start=int(start))

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
