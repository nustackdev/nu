"""Ordering ops: a keyed, ordered collection of children, on Row, Column, a flowing Grid and List.

A key is the child's identity and stays with it; where it draws is a place
in the container's order, which the browser keeps. ``insert``, ``move``,
``remove``, ``truncate``, ``keep`` and ``set_order`` each ship one frame that
the browser applies to the order it holds, so the server never needs to know
which children are there:

- until one of them runs, children draw in the default order: positions by
  number, names in the order first written
- the first one writes the order down as it is drawn, and from then on the
  container keeps it: a key nothing placed (a child written later) draws
  after the placed ones, in the default order among themselves
- ``insert`` and ``move`` change one place, nothing else is rewritten;
  ``at`` counts places from the front
- ``remove``, ``truncate`` and ``keep`` drop children and their places
  together. ``ref[k].erase()`` drops the child only: its place stays, so a
  child written there again comes back where it was

Per child layout (``grow``, ``align_self``, ...) is keyed by the same keys,
so it moves with its child. A placed grid has places of its own (``[r, c]``)
and refuses every op here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms import List as ListOf
from nu.lang import Nu
from nu.lang.sentinels import UNSET
from nustd.ui.core import ItemRef, Send, check_key


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.lang.args import IntArg, ListArg
    from nustd.ui.core import Ref


__all__ = [
    "InsertItem",
    "KeepItems",
    "MoveItem",
    "OrderItems",
    "Ordered",
    "RemoveItem",
    "TruncateItems",
]


# Each op ships a frame on the container itself; the browser applies it to
# the order it keeps. Keys go out as the text segment the child sits at
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
    """Drop the child at ``key`` and its place. A key the container does not have is a no-op."""

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


class Ordered:
    """The ordering ops, for a container whose children are keyed and ordered."""

    def _check_ordered(self, op: str) -> None:
        """Refuse ``op`` when this container has no order of keys (a placed grid)."""

    def insert(
        self,
        item: object,
        *,
        at: IntArg = UNSET,
        before: object = UNSET,
        after: object = UNSET,
    ) -> Nu:
        """Give a child a place: at the end, ``at`` a position, or ``before``/``after`` a key.

        ``item`` is a key (``"k"``, ``3``) or a child of this container
        (``row["k"].to(CardRef)``, or ``row["k"]`` with ``item=``). A key
        only places: the child shows there once something writes it. A
        typed child is brought on screen too, as declared, right after it is
        placed. A key already placed moves.
        """
        self._check_ordered("insert")
        child: ItemRef | None = None
        if isinstance(item, ItemRef):
            child = item
            item = self._key_of_child(item)  # type: ignore[attr-defined]
        key = self._key("insert", item)
        place = InsertItem(self, _segment(key), *self._anchor("insert", at, before, after))  # type: ignore[arg-type]
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
        self._check_ordered("move")
        key = self._key("move", key)
        return MoveItem(self, _segment(key), *self._anchor("move", at, before, after))  # type: ignore[arg-type]

    def remove(self, key: object) -> Nu:
        """Drop the child at ``key`` and its place. A key the container does not have is a no-op."""
        self._check_ordered("remove")
        return RemoveItem(self, _segment(self._key("remove", key)))  # type: ignore[arg-type]

    def truncate(self, count: IntArg) -> Nu:
        """Keep the first ``count`` places and drop every child after them."""
        self._check_ordered("truncate")
        if isinstance(count, bool) or (isinstance(count, int) and count < 0):
            msg = f"{self._owner_name()}.truncate takes a count >= 0, not {count!r}"  # type: ignore[attr-defined]
            raise ValueError(msg)
        return TruncateItems(self, count)  # type: ignore[arg-type]

    def keep(self, keys: ListArg[str] | Iterable[object]) -> Nu:
        """Keep the children at ``keys`` where they are and drop every other one."""
        self._check_ordered("keep")
        return KeepItems(self, self._keys("keep", keys))  # type: ignore[arg-type]

    def set_order(self, keys: ListArg[str] | Iterable[object]) -> Nu:
        """Put the children at ``keys`` first, in that order; the rest keep theirs after.

        Ships ``order_items``: it orders a container's children. A
        DataTable's ``set_order`` is another op (``set_order``) on its rows.
        """
        self._check_ordered("set_order")
        return OrderItems(self, self._keys("set_order", keys))  # type: ignore[arg-type]

    def _key(self, op: str, key: object) -> object:
        owner = f"{self._owner_name()}.{op}"  # type: ignore[attr-defined]
        return check_key(
            owner,
            key,
            positions=self._positions,  # type: ignore[attr-defined]
            names=self._names,  # type: ignore[attr-defined]
            parts=self._parts,  # type: ignore[attr-defined]
        )

    def _keys(self, op: str, keys: object) -> object:
        if isinstance(keys, Nu):
            return keys
        if isinstance(keys, (str, bytes)) or not hasattr(keys, "__iter__"):
            msg = f"{self._owner_name()}.{op} takes a list of keys, not {keys!r}"  # type: ignore[attr-defined]
            raise TypeError(msg)
        return ListOf.of(*(_segment(self._key(op, k)) for k in keys))  # type: ignore[union-attr]

    def _anchor(
        self, op: str, at: object, before: object, after: object
    ) -> tuple[str | None, object]:
        owner = self._owner_name()  # type: ignore[attr-defined]
        given = [
            (n, v) for n, v in (("at", at), ("before", before), ("after", after)) if v is not UNSET
        ]
        if len(given) > 1:
            names = " and ".join(n for n, _ in given)
            msg = f"{owner}.{op} takes one of at, before, after, not {names}"
            raise TypeError(msg)
        if not given:
            return None, None
        name, value = given[0]
        if name == "at":
            if isinstance(value, bool) or not isinstance(value, (int, Nu)):
                msg = f"{owner}.{op}: at is a position (int), not {value!r}"
                raise TypeError(msg)
            if isinstance(value, int) and value < 0:
                msg = f"{owner}.{op}: at counts from the front, use a position >= 0, not {value}"
                raise IndexError(msg)
            return name, value
        return name, _segment(self._key(op, value))
