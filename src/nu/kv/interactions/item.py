"""Leaf-level KV atoms: read, write and delete one primitive at one address.

Every atom here holds a leaf Ref at slot 0 and reaches the value through the
Ref's *parent* view, resolving the parent chain and the leaf address from the
Ref rather than from the value itself. That is the whole shape: a leaf Ref
plus, for the writers, a value at slot 1.

The ones spelled ``Unsafe`` skip the checks the ordinary shape ops make -
node-type lookup, container-vs-primitive validation, existence of the parent
chain - and go straight to a single ``ctx.get`` / ``ctx.put`` / ``ctx.delete``.
That is what buys them their speed and what makes them wrong to reach for by
hand: they are the target a tree deformer rewrites ordinary reads and writes
into once it has proved the chain exists and the child is a primitive. The
caller carries both guarantees.

They also demand a substrate that has the operations at all: a virtuals view
with ``UnsafePrimitiveOpsBase`` in its MRO. A view without it fails at the
attribute, not at a check.

Sorts: ``ItemPrimitiveGetUnsafe`` is a ScalarQuery. The rest are Commands and
declare slot 0 as a mutation position, so ``auto_flow_atomic`` sees them as
writes and braces them in a Transaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "InitItemCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class InitItemCmd(Command):
    """Walks a container Ref's path and drops the view it lands on.

    Resolves the Ref's path and opens the view at the end of it, discarding
    the result. The walk is pure navigation - it opens containers, it does
    not create them - so on a path of static addresses it does not touch
    storage at all.

    Args:
        ref: the container Ref to walk to. Must be a ``ViewRef``; a leaf
            ``PrimitiveRef`` has no view of its own to open.

    Notes:
        - Declares slot 0 as a mutation position even though it writes
          nothing, so a Flow branch holding it is braced in a Transaction
          rather than a Snapshot.
        - Raises KeyError or IndexError when an address along the path does
          not normalize, the way a plain read of that Ref would.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            ref._fetch(rt, _child_nid(rt, nid, 0))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._afetch(rt, _child_nid(rt, nid, 0))

        return athunk


class ItemPrimitiveGetUnsafe(ScalarQuery):
    """Reads one primitive off a Ref's parent view in a single storage get.

    Resolves the Ref's parent view and leaf address, then does one ``ctx.get``
    against it. No node-type lookup, no primitive assertion, no check that the
    parent chain exists: an absent chain is a storage-level miss, which reads
    back the same as an absent value.

    Args:
        ref: the leaf Ref to read. Its parent must be a view carrying
            ``UnsafePrimitiveOpsBase``, and its child must be a primitive.

    Notes:
        - Reads through whatever snapshot or transaction is on the ctx, so
          it sees a Transaction's own uncommitted writes.
        - Does not create anything. A missing parent chain stays missing.

    Yields:
        The stored value. EMPTY when nothing is stored at the address, and
        also when the substrate hands back INVALID - the two collapse to one
        answer here, so this atom never yields INVALID.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Snapshot(ItemPrimitiveGetUnsafe(State.counters["hits"])),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            address = ref._address(rt, cnid)
            value = parent._unsafe_primitive_read(address)
            return EMPTY if value is EMPTY or value is INVALID else value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            address = await ref._aaddress(rt, cnid)
            value = parent._unsafe_primitive_read(address)
            return EMPTY if value is EMPTY or value is INVALID else value

        return athunk


class _UnsafeSetBase(Command):
    """Shared base: resolve parent view + address + value, then unsafe-write.

    Subclasses differ only in ``_ensure_exists``, which decides whether the
    parent chain is created before the put.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _ensure_exists: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value_thunk = children[1]
        ensure = self._ensure_exists

        def thunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            address = ref._address(rt, cnid)
            value = value_thunk(rt)
            if value is EMPTY or value is INVALID:
                raise ValueError("cannot store sentinel value")
            parent._unsafe_primitive_write(address, value, ensure_exists=ensure)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value_thunk = children[1]
        ensure = self._ensure_exists

        async def athunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            address = await ref._aaddress(rt, cnid)
            value = await value_thunk(rt)
            if value is EMPTY or value is INVALID:
                raise ValueError("cannot store sentinel value")
            parent._unsafe_primitive_write(address, value, ensure_exists=ensure)

        return athunk


class ItemPrimitiveSetUnsafeCmd(_UnsafeSetBase):
    """Writes one primitive, creating the parent chain first if it is missing.

    The self-sufficient unsafe writer: it still skips node-type lookup and the
    primitive assertion, but it does call ``ensure_created`` on the parent view
    before the put, so it does not need an ``InitItemCmd`` ahead of it. Use
    this one unless the chain is provably already there.

    Args:
        ref: the leaf Ref to write to.
        value: evaluated then stored as-is, with no decomposition. A
            container lands as one opaque blob.

    Notes:
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - The value is evaluated after the parent view and address resolve.
        - Raises ``ValueError`` when the value slot evaluates to EMPTY or
          INVALID; sentinels are never stored.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Transaction(
                ItemPrimitiveSetUnsafeCmd(State.counters["hits"], 1),
            ),
        )
    """

    _ensure_exists = True


class ItemPrimitiveSetUnsafeParentSkipCmd(_UnsafeSetBase):
    """Writes one primitive as a bare put, assuming the parent chain exists.

    The fastest write in the fabric and the one with no safety net at all: it
    skips even the ``ensure_created`` that ``ItemPrimitiveSetUnsafeCmd`` keeps.
    The caller owes the parent chain, normally by having run one ordinary
    write, or one ``ItemPrimitiveSetUnsafeCmd``, before the hot loop. Writing
    under a chain that was never created leaves an orphan key that the
    container's own scan never sees.

    Args:
        ref: the leaf Ref to write to.
        value: evaluated then stored as-is, with no decomposition.

    Notes:
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - Raises ``ValueError`` when the value slot evaluates to EMPTY or
          INVALID; sentinels are never stored.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Transaction(
                ItemPrimitiveSetUnsafeCmd(State.counters["hits"], 0),
                nu.ForeverDo(
                    ItemPrimitiveSetUnsafeParentSkipCmd(State.counters["hits"], 1),
                ),
            ),
        )
    """

    _ensure_exists = False


class ItemPrimitiveDeleteUnsafeCmd(Command):
    """Deletes one primitive as a bare storage delete.

    Args:
        ref: the leaf Ref whose value is removed.

    Notes:
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - Deleting an address that holds nothing is a no-op, not an error.
        - Removes only the leaf. The containers above it stay, so the parent
          chain remains valid for later writes.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Transaction(
                ItemPrimitiveDeleteUnsafeCmd(State.counters["hits"]),
            ),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            parent._unsafe_primitive_delete(ref._address(rt, cnid))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            parent._unsafe_primitive_delete(await ref._aaddress(rt, cnid))

        return athunk


class ItemPrimitiveSetCmd(Command):
    """Stores a whole value as one opaque blob under a Ref, container or not.

    The safe writer of the group, and the only one here that does not need
    ``UnsafePrimitiveOpsBase``: it goes through the parent view's
    ``_primitive_write``, which creates the container chain and then puts the
    value at a single key. What it bypasses is decomposition, not safety - an
    ordinary set fans a list or dict out into per-element storage, this one
    keeps it whole.

    That is what backs ``PrimitiveListRef``, ``PrimitiveDictRef`` and
    ``PrimitiveSetRef``: containers that should round-trip as one object
    rather than shape-decompose.

    Args:
        ref: the leaf Ref to write to.
        value: evaluated then stored whole, whatever its structure.

    Notes:
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - The value is evaluated before the parent view resolves, the reverse
          of the unsafe writers' order.
        - Raises ``ValueError`` when the value slot evaluates to EMPTY or
          INVALID; sentinels are never stored.

    Yields:
        Nothing.

    Example:
        class State(nu.Shape):
            raw = nu.kv.PrimitiveListRef.slot()

        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Transaction(ItemPrimitiveSetCmd(State.raw, [1, 2, 3])),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        data_thunk = children[1]

        def thunk(rt: Runtime) -> None:
            data = data_thunk(rt)
            if data is EMPTY or data is INVALID:
                raise ValueError("cannot store sentinel value")
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            parent._primitive_write(ref._address(rt, cnid), data)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        data_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            data = await data_thunk(rt)
            if data is EMPTY or data is INVALID:
                raise ValueError("cannot store sentinel value")
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            parent._primitive_write(await ref._aaddress(rt, cnid), data)

        return athunk
