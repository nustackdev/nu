"""kv blob containers: a whole collection held as one leaf value.

A blob is written and read whole, with no per-element addresses, so it holds
heterogeneous or opaque contents that should round-trip exactly as written.
Each mixes in its collection form, so the value still carries the full
collection surface; the decomposed containers are the other choice.

A mutation written on a list, dict or set blob (``rows.append(2)``) persists:
in a mutation slot the ref evaluates to a write-through value that stores the
whole blob back after each mutating call. Everywhere else it reads as a plain
value, so nothing tied to the storage context leaves the read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

import nu
from nu.forms import Dict, FrozenSet, List, Set, Tuple
from nu.lang import Effect
from nu.lang.null import is_null

from ..views import PrimitiveDictView, PrimitiveListView, PrimitiveSetView
from .items import ItemRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Arg
    from nu.lang.runtime import Runtime

    from ..views.writeback import _WriteThrough


__all__ = [
    "PrimitiveDictRef",
    "PrimitiveFrozenSetRef",
    "PrimitiveListRef",
    "PrimitiveSetRef",
    "PrimitiveTupleRef",
]


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def _in_mutation_slot(rt: Runtime, nid: int, term: object) -> bool:
    """Whether the term at ``nid`` sits in a slot its parent declares it writes."""
    parent = rt.program.parent_id[nid]
    if parent < 0:
        return False
    return any(
        child is term and effect is Effect.WRITE
        for child, effect in nu.tree.node_effects(rt.program.terms[parent])  # type: ignore[arg-type]
    )


class _WriteBackRef(ItemRef):
    """A mutable blob: in a mutation slot it evaluates to a write-through value.

    A core mutation (``Append``, ``SetItem``, ``AddCmd``, ...) calls the native
    method on what its target evaluates to. Here that is ``_writeback``: the stored
    value wrapped so each mutating call stores the whole blob back through the
    parent view it was read from, under the same storage context.
    """

    _writeback: ClassVar[type[_WriteThrough]]

    def _read_for(self, rt: Runtime, nid: int, path: tuple) -> object:
        parent = self._fetch_parent_view(rt, path)
        value = self._read_from(parent, path)
        if is_null(value) or not _in_mutation_slot(rt, nid, self):
            return value
        return self._writeback(value, parent, path[-1][0])  # type: ignore[call-arg]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._read_for(rt, nid, self._resolve_path(rt, nid))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._read_for(rt, nid, await self._aresolve_path(rt, nid))

        return athunk


class PrimitiveListRef(_WriteBackRef, List[T], Generic[T]):
    """A list leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Stored as one opaque value, so the elements get no addresses of
          their own and cannot be reached or watched individually.
        - Reads come back as a real Python list, so heterogeneous and nested
          contents round-trip as they were written.
        - ``set`` writes a whole list. The element-level mutations
          (``append``, ``insert``, ``del_at``, ...) persist too: each one
          stores the whole blob back, so it costs one full write.
        - A nested value mutated in place does not persist; write the
          element back with ``set_at``.
        - ListRef is the other choice: it decomposes into per-index storage
          and gives per-element navigation.

    Example:
        class Bag(Shape):
            rows = PrimitiveListRef.slot()
        run(Bag.rows.set([1, "two", {"three": 3}]), ctx)
        run(Bag.rows, ctx)
    """

    _writeback = PrimitiveListView

    def _lift(self, raw: object) -> list:
        """Return the stored value as a plain list."""
        return raw if isinstance(raw, list) else list(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[list[T]]) -> object:
        """Store the whole list as one leaf value.

        Args:
            value: the list to store. May be a literal or an expression.

        Notes:
            - Overrides the decomposing slot write, so the list lands as one
              opaque value with no per-index children underneath it.
            - Replaces whatever was there; there is no merge with the value
              already stored.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.rows.set([1, "two"]), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveDictRef(_WriteBackRef, Dict[K, V], Generic[K, V]):
    """A dict leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Stored as one opaque value, so the keys get no addresses of their
          own and cannot be reached or watched individually.
        - Reads come back as a real Python dict, nested contents included.
        - ``set`` writes a whole dict. The key-level mutations
          (``set_item``, ``pop``, ``update``, ...) persist too: each one
          stores the whole blob back, so it costs one full write.
        - A nested value mutated in place does not persist; write the
          entry back with ``set_item``.
        - DictRef is the other choice: it decomposes into per-key storage
          and gives per-key navigation and change observation.

    Example:
        class Bag(Shape):
            meta = PrimitiveDictRef.slot()
        run(Bag.meta.set({"a": 1, "b": [2, 3]}), ctx)
        run(Bag.meta, ctx)
    """

    _writeback = PrimitiveDictView

    def _lift(self, raw: object) -> dict:
        """Return the stored value as a plain dict."""
        return raw if isinstance(raw, dict) else dict(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[dict[K, V]]) -> object:
        """Store the whole dict as one leaf value.

        Args:
            value: the dict to store. May be a literal or an expression.

        Notes:
            - Overrides the decomposing slot write, so the dict lands as one
              opaque value with no per-key children underneath it.
            - Replaces whatever was there; keys already stored are not
              merged in.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.meta.set({"a": 1}), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveTupleRef(ItemRef, Tuple):
    """A tuple leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python tuple, so the type survives the
          round trip rather than degrading to a list.
        - Has no decomposing counterpart: a tuple slot is always stored
          whole.
        - Elements get no addresses of their own, so nothing under it can be
          reached or watched individually.

    Example:
        class Bag(Shape):
            pair = PrimitiveTupleRef.slot()
        run(Bag.pair.set((1, "two")), ctx)
        run(Bag.pair, ctx)
    """

    def _lift(self, raw: object) -> tuple:
        """Return the stored value as a plain tuple."""
        return raw if isinstance(raw, tuple) else tuple(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[tuple]) -> object:
        """Store the whole tuple as one leaf value.

        Args:
            value: the tuple to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.pair.set((1, "two")), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveSetRef(_WriteBackRef, Set[T], Generic[T]):
    """A set leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python set, so membership and the set
          operators work on the value as they would in Python.
        - ``set`` writes a whole set. The element-level mutations (``add``,
          ``discard``, ``update``, ...) persist too: each one stores the
          whole blob back, so it costs one full write.
        - SetRef is the other choice: it decomposes into per-element storage
          and gives change observation.

    Example:
        class Bag(Shape):
            members = PrimitiveSetRef.slot()
        run(Bag.members.set({1, 2, 3}), ctx)
        run(Bag.members, ctx)
    """

    _writeback = PrimitiveSetView

    def _lift(self, raw: object) -> set:
        """Return the stored value as a plain set."""
        return raw if isinstance(raw, set) else set(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[set[T]]) -> object:
        """Store the whole set as one leaf value.

        Args:
            value: the set to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there; it is not a union with the set
              already stored.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.members.set({1, 2}), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)


class PrimitiveFrozenSetRef(ItemRef, FrozenSet[T], Generic[T]):
    """A frozenset leaf in KV storage, written and read back whole as one blob.

    Notes:
        - Reads come back as a real Python frozenset, so the type survives
          the round trip.
        - Carries the read-only set surface only: union, intersection and
          the rest yield new values and never touch storage.
        - Has no decomposing counterpart; a frozenset slot is always stored
          whole.

    Example:
        class Bag(Shape):
            locked = PrimitiveFrozenSetRef.slot()
        run(Bag.locked.set(frozenset({1, 2})), ctx)
        run(Bag.locked, ctx)
    """

    def _lift(self, raw: object) -> frozenset:
        """Return the stored value as a plain frozenset."""
        return raw if isinstance(raw, frozenset) else frozenset(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[frozenset[T]]) -> object:
        """Store the whole frozenset as one leaf value.

        Args:
            value: the frozenset to store. May be a literal or an expression.

        Notes:
            - Replaces whatever was there.

        Yields:
            Nothing. It is a command, run for the write.

        Example:
            run(Bag.locked.set(frozenset({1, 2})), ctx)
        """
        from ..interactions import ItemPrimitiveSetCmd

        return ItemPrimitiveSetCmd(self, value)
