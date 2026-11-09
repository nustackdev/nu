"""Ordered dict atoms: place, move and read the ends of an ordered collection.

An ``OrderedDictRef`` names a container whose ids keep the order they were
placed in. These atoms are the ordering side of it: two put a new id next to
an existing one, one moves an id next to another, two read the ends. Mapping
reads and writes go through the ordinary dict ops.

Every atom takes the container Ref at slot 0 and its ids as ordinary children,
so an id can be another Ref read at run time rather than a value fixed when
the tree was written. Each one is a single view method call, so it costs one
round trip when the view is proxied.

None is written directly in normal use. ``OrderedDictRef.insert_before``,
``insert_after``, ``move``, ``first`` and ``last`` build them, already wrapped
in the ``Object`` form. A log dict keeps an order too, the order its ids were
first set, so ``LogDictRef.first`` and ``last`` read its ends with the same two
atoms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.null import is_null


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "OrderedFirst",
    "OrderedInsertAfterCmd",
    "OrderedInsertBeforeCmd",
    "OrderedLast",
    "OrderedMoveCmd",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


def _guard_ids(*ids: object) -> None:
    """Refuse a NULL id before the view is touched, as ``SetItem`` does."""
    for i in ids:
        if is_null(i):
            raise ValueError("cannot write with a NULL operand")


class _InsertBase(Command):
    """Shared base: fetch the view, then place ``id`` next to ``anchor``.

    Subclasses differ only in ``_after``, which picks the side of the anchor.
    Children are ``(ref, anchor, id, value)``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _after: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, anchor_thunk, id_thunk, value_thunk = children
        after = self._after

        def thunk(rt: Runtime) -> None:
            anchor = anchor_thunk(rt)
            key = id_thunk(rt)
            value = value_thunk(rt)
            _guard_ids(anchor, key)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            if after:
                view.insert_after(anchor, key, value)
            else:
                view.insert_before(anchor, key, value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, anchor_thunk, id_thunk, value_thunk = children
        after = self._after

        async def athunk(rt: Runtime) -> None:
            anchor = await anchor_thunk(rt)
            key = await id_thunk(rt)
            value = await value_thunk(rt)
            _guard_ids(anchor, key)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            if after:
                view.insert_after(anchor, key, value)
            else:
                view.insert_before(anchor, key, value)

        return athunk


class OrderedInsertBeforeCmd(_InsertBase):
    """Adds a new id directly before an id already in the collection.

    Args:
        ref: the ordered container Ref to write to.
        anchor: the id to place the new one in front of.
        id: the id to add.
        value: what the id holds; a plain mapping is decomposed under it.

    Notes:
        - ``anchor``, ``id`` and ``value`` are children, so each may be a Ref
          read at run time; a raw value is wrapped as a Literal.
        - Raises ValueError when ``id`` is already present or any operand
          reads NULL, and KeyError when ``anchor`` is not present. None of
          these is swallowed.
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - Never creates the container: the anchor has to exist already, so
          the first id goes in with ``set_item``.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nustd.kv.memory_navigator(),
            body=nustd.kv.Transaction(
                OrderedInsertBeforeCmd(Board.cells, "c2", "c1", True)
            ),
        )
    """

    _after = False


class OrderedInsertAfterCmd(_InsertBase):
    """Adds a new id directly after an id already in the collection.

    Same contract as ``OrderedInsertBeforeCmd``, placed on the other side of
    ``anchor``.

    Args:
        ref: the ordered container Ref to write to.
        anchor: the id to place the new one behind.
        id: the id to add.
        value: what the id holds; a plain mapping is decomposed under it.

    Yields:
        Nothing.
    """

    _after = True


class OrderedMoveCmd(Command):
    """Moves an id already in the collection next to another id.

    The value under the id is untouched; only its place changes. Exactly one
    of ``before`` and ``after`` names the neighbour.

    Args:
        ref: the ordered container Ref to write to.
        id: the id to move.
        before: the id to land in front of, or None.
        after: the id to land behind, or None.

    Notes:
        - ``id``, ``before`` and ``after`` are children, so each may be a Ref
          read at run time; a raw value is wrapped as a Literal.
        - Raises ValueError when neither or both of ``before`` and ``after``
          are given or any operand reads NULL (a NULL neighbour is a bad
          id, not an omitted one), and KeyError when either id is absent.
        - Moving an id next to itself, or to where it already is, is a no-op.
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nustd.kv.memory_navigator(),
            body=nustd.kv.Transaction(OrderedMoveCmd(Board.cells, "c3", "c1", None)),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    @staticmethod
    def _check(key: object, before: object, after: object) -> None:
        _guard_ids(key, before, after)
        if (before is None) == (after is None):
            raise ValueError("move takes exactly one of before= or after=")

    @staticmethod
    def _place(view: object, key: object, before: object, after: object) -> None:
        if before is not None:
            view.move_before(key, before)  # type: ignore[attr-defined]
        else:
            view.move_after(key, after)  # type: ignore[attr-defined]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, id_thunk, before_thunk, after_thunk = children

        def thunk(rt: Runtime) -> None:
            key, before, after = id_thunk(rt), before_thunk(rt), after_thunk(rt)
            self._check(key, before, after)
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            self._place(view, key, before, after)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, id_thunk, before_thunk, after_thunk = children

        async def athunk(rt: Runtime) -> None:
            key, before, after = await id_thunk(rt), await before_thunk(rt), await after_thunk(rt)
            self._check(key, before, after)
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            self._place(view, key, before, after)

        return athunk


class _EdgeBase(ScalarQuery):
    """Shared base: fetch the view and read one end of the order.

    Subclasses differ only in ``_last``. One seek, whatever the size. The view
    keeps the order and reads its ends (``first()`` / ``last()``): an ordered
    dict view or a log dict view, which raises IndexError when empty.
    """

    _last: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        last = self._last

        def thunk(rt: Runtime) -> object:
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            return view.last() if last else view.first()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        last = self._last

        async def athunk(rt: Runtime) -> object:
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            return view.last() if last else view.first()

        return athunk


class OrderedFirst(_EdgeBase):
    """Reads the first id of an ordered collection, in one seek.

    Args:
        ref: the ordered or log container Ref to read.

    Notes:
        - Cost is one seek, independent of how many ids the collection holds.
        - Raises IndexError on an empty collection, as ``seq[0]`` does.
        - Safe on a Snapshot: a missing container is never created.

    Yields:
        The first id.

    Example:
        app = nu.With(
            nustd.kv.memory_navigator(),
            body=nustd.kv.Snapshot(OrderedFirst(Board.cells)),
        )
    """

    _last = False


class OrderedLast(_EdgeBase):
    """Reads the last id of an ordered collection, in one seek.

    Same contract as ``OrderedFirst``, from the other end.

    Args:
        ref: the ordered or log container Ref to read.

    Yields:
        The last id.
    """

    _last = True
