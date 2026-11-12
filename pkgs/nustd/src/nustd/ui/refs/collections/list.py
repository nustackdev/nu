"""``ListRef`` -- a bulleted or numbered list whose items are any nodes.

A container. Plain string items render first, from the ``items`` prop, the
way the list always drew; then every child node is one more item after
them. Positions (``lst[0]``) draw in index order; names (``lst["k"]``) in
the order they were first written. There is no item Ref: any child is
an item, so a Badge, a Link or a whole Row can each be one.

The string half stays for compatibility and because short text lists are
common: ``set(items)`` replaces the strings whole, ``append`` adds one to
the end, ``clear`` empties them, and none of the three touches the child
nodes. That makes it the one container with a ``set()`` that is not chrome.

The child half is the keyed, ordered, dynamic collection. A key is the
child's identity and stays with it; where it draws is a place in the list's
order, which the browser keeps. ``insert``, ``move``, ``remove``,
``truncate``, ``keep`` and ``set_order`` each ship one frame that the
browser applies to the order it holds, so the server never needs to know
which children are there:

- until one of them runs, children draw in the default order: positions by
  number, names in the order first written
- the first one writes the order down as it is drawn, and from then on the
  list keeps it: a key nothing placed (a child written later) draws after
  the placed ones, in the default order among themselves
- ``insert`` and ``move`` change one place, nothing else is rewritten;
  ``at`` counts places from the front
- ``remove``, ``truncate`` and ``keep`` drop children and their places
  together. ``lst[k].erase()`` drops the child only: its place stays, so a
  child written there again comes back where it was

The ops reorder children only; the string items always draw first.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.forms import List as ListOf
from nu.lang import Nu
from nu.lang.sentinels import UNSET
from nustd.ui.core import Append, ItemRef, Send, Write, check_key

from .base import ListCollectionRef


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.domains.shape import Slot
    from nu.lang.args import IntArg, ListArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = [
    "InsertItem",
    "KeepItems",
    "ListRef",
    "MoveItem",
    "OrderItems",
    "RemoveItem",
    "TruncateItems",
]


ListVariant = Literal["bullet", "number"]


# ---- child ops --------------------------------------------------------------
#
# Each one ships a frame on the list itself; the browser's ListRef applies it
# to the order it keeps. Keys go out as the text segment the child sits at
# (``0`` -> ``"0"``), the same text its address ships as.


def _segment(key: object) -> object:
    """A key as the wire segment: an int or a str as text, a term as given."""
    return key if isinstance(key, Nu) else str(key)


class _PlacedOp(Send):
    """A child op that names a place: ``at`` a position, or ``before``/``after`` a key.

    Which one rides the payload (``_payload["anchor"]``, so it survives a
    tree rewrite); none means the end.
    """

    def __init__(self, ref: Ref, key: object, anchor: str | None, value: object) -> None:
        if anchor is None:
            super().__init__(ref, key)
        else:
            super().__init__(ref, key, value)
        self._payload["anchor"] = anchor

    def _frame_payload(self, values: list[object]) -> object:
        payload: dict[str, object] = {"key": str(values[0])}
        anchor = self._payload.get("anchor")
        if anchor == "at":
            payload["at"] = int(values[1])  # type: ignore[call-overload]
        elif anchor is not None:
            payload[anchor] = str(values[1])
        return payload


class InsertItem(_PlacedOp):
    """Give ``key`` a place; a key already placed moves there.

    Payload ``{key, at | before | after}``, none of the three meaning the
    end. A place may come before its child: the child drawn there later
    shows in it.
    """


class MoveItem(_PlacedOp):
    """Move the child at ``key`` to a new place. Same payload as ``InsertItem``."""


class RemoveItem(Send):
    """Drop the child at ``key`` and its place. A key the list does not have is a no-op."""

    def _frame_payload(self, values: list[object]) -> object:
        return {"key": str(values[0])}


class TruncateItems(Send):
    """Keep the first ``count`` places, drop every child after them."""

    def _frame_payload(self, values: list[object]) -> object:
        return {"count": int(values[0])}  # type: ignore[call-overload]


class KeepItems(Send):
    """Keep the children at ``keys`` where they are, drop every other one."""

    def _frame_payload(self, values: list[object]) -> object:
        return {"keys": [str(k) for k in values[0]]}  # type: ignore[attr-defined]


class OrderItems(Send):
    """Put the children at ``keys`` first, in that order; the rest keep theirs after."""

    def _frame_payload(self, values: list[object]) -> object:
        return {"keys": [str(k) for k in values[0]]}  # type: ignore[attr-defined]


def _same_place(a: object, b: object) -> bool:
    """Whether two refs name one place: same kinds and segments all the way up."""
    while a is not None and b is not None:
        if a is b:
            return True
        if type(a) is not type(b):
            return False
        sa, sb = a._payload.get("segment"), b._payload.get("segment")  # type: ignore[attr-defined]
        if isinstance(sa, Nu) or isinstance(sb, Nu):
            if sa is not sb:
                return False
        elif sa != sb:
            return False
        a, b = a._parent, b._parent  # type: ignore[attr-defined]
    return a is None and b is None


class ListRef(ListCollectionRef):
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

    # ``lst[0]`` and ``lst["k"]`` both: positions draw in number order, names
    # in the order first written, all after the string items.
    _names: ClassVar[bool] = True

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
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

    # --- the child collection ------------------------------------------------

    def insert(
        self,
        item: object,
        *,
        at: IntArg = UNSET,
        before: object = UNSET,
        after: object = UNSET,
    ) -> Nu:
        """Give a child a place: at the end, ``at`` a position, or ``before``/``after`` a key.

        ``item`` is a key (``"k"``, ``3``) or a child of this list
        (``lst["k"].to(CardRef)``, or ``lst["k"]`` with ``item=``). A key
        only places: the child shows there once something writes it. A
        typed child is brought on screen too, as declared, right after it is
        placed. A key already placed moves.
        """
        child: ItemRef | None = None
        if isinstance(item, ItemRef):
            if not _same_place(item._parent, self):
                msg = (
                    f"{self._owner_name()}.insert takes a child of this list or a key, not {item!r}"
                )
                raise ValueError(msg)
            child = item
            item = item._payload.get("segment")
        key = self._key("insert", item)
        place = InsertItem(self, _segment(key), *self._anchor("insert", at, before, after))
        if child is None or type(child) is ItemRef:
            return place
        return place >> child.init()

    def move(
        self,
        key: object,
        *,
        at: IntArg = UNSET,
        before: object = UNSET,
        after: object = UNSET,
    ) -> Nu:
        """Move the child at ``key``: to the end, ``at`` a position, or ``before``/``after`` a key.

        Only its place changes; the child and every other place stay as
        they are.
        """
        key = self._key("move", key)
        return MoveItem(self, _segment(key), *self._anchor("move", at, before, after))

    def remove(self, key: object) -> Nu:
        """Drop the child at ``key`` and its place. A key the list does not have is a no-op."""
        return RemoveItem(self, _segment(self._key("remove", key)))

    def truncate(self, count: IntArg) -> Nu:
        """Keep the first ``count`` places and drop every child after them."""
        if isinstance(count, bool) or (isinstance(count, int) and count < 0):
            msg = f"{self._owner_name()}.truncate takes a count >= 0, not {count!r}"
            raise ValueError(msg)
        return TruncateItems(self, count)

    def keep(self, keys: ListArg[str] | Iterable[object]) -> Nu:
        """Keep the children at ``keys`` where they are and drop every other one."""
        return KeepItems(self, self._keys("keep", keys))

    def set_order(self, keys: ListArg[str] | Iterable[object]) -> Nu:
        """Put the children at ``keys`` first, in that order; the rest keep theirs after."""
        return OrderItems(self, self._keys("set_order", keys))

    def _key(self, op: str, key: object) -> object:
        owner = f"{self._owner_name()}.{op}"
        return check_key(
            owner, key, positions=self._positions, names=self._names, parts=self._parts
        )

    def _keys(self, op: str, keys: object) -> object:
        if isinstance(keys, Nu):
            return keys
        if isinstance(keys, (str, bytes)) or not hasattr(keys, "__iter__"):
            msg = f"{self._owner_name()}.{op} takes a list of keys, not {keys!r}"
            raise TypeError(msg)
        return ListOf.of(*(_segment(self._key(op, k)) for k in keys))  # type: ignore[union-attr]

    def _anchor(
        self, op: str, at: object, before: object, after: object
    ) -> tuple[str | None, object]:
        given = [
            (n, v) for n, v in (("at", at), ("before", before), ("after", after)) if v is not UNSET
        ]
        if len(given) > 1:
            names = " and ".join(n for n, _ in given)
            msg = f"{self._owner_name()}.{op} takes one of at, before, after, not {names}"
            raise TypeError(msg)
        if not given:
            return None, None
        name, value = given[0]
        if name == "at":
            if isinstance(value, bool) or not isinstance(value, (int, Nu)):
                msg = f"{self._owner_name()}.{op}: at is a position (int), not {value!r}"
                raise TypeError(msg)
            if isinstance(value, int) and value < 0:
                msg = f"{self._owner_name()}.{op}: at counts from the front, use a position >= 0, not {value}"
                raise IndexError(msg)
            return name, value
        return name, _segment(self._key(op, value))
