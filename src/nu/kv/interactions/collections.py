"""Container-level KV atoms: sweep every direct primitive child at once.

Both atoms hold a container Ref at slot 0, fetch the view it names, and act on
the whole child set in one storage sweep rather than one address at a time.

Like their leaf-level siblings in ``item``, they are ``Unsafe`` because they
assume every direct child is a primitive: they use the container's raw scan
filter and do not look up node types. A nested container under the same view
is not something they handle, it is something the caller has ruled out. They
need a virtuals view carrying ``UnsafePrimitiveOpsBase``.

The two differ on a missing container: the scan swallows the navigation error
and reports emptiness, the clear lets it out.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "ClearPrimitivesUnsafeCmd",
    "ScanPrimitivesUnsafe",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class ScanPrimitivesUnsafe(ScalarQuery):
    """Reads every direct primitive value under a container in one raw scan.

    One prefix-and-length filtered scan over the container's own level, so
    the cost is the values themselves rather than a lookup per address.
    Nothing distinguishes a primitive from a container marker here, so a
    nested container under the same view would come back as its raw marker
    rather than being skipped.

    Args:
        ref: the container Ref to scan. Its view must carry
            ``UnsafePrimitiveOpsBase``, and its direct children must all be
            primitives.

    Notes:
        - A ScalarQuery, so the whole scan is one value on the tree, not a
          stream. What it hands back is lazy all the same, so the storage
          read happens as the consumer pulls, inside whatever bracket is
          still open.
        - Values arrive in the container's own storage order.

    Yields:
        A generator of the stored values. EMPTY when the container is not
        reachable - a missing address along the Ref's path is answered as
        emptiness, not raised.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Snapshot(
                nu.Collect(nu.Iter(ScanPrimitivesUnsafe(State.counters))),
            ),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            try:
                view = ref._fetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            return view._unsafe_primitive_scan_values()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            try:
                view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            return view._unsafe_primitive_scan_values()

        return athunk


class ClearPrimitivesUnsafeCmd(Command):
    """Deletes every direct primitive child of a container, keeping the container.

    Scans the container's own level and deletes each key it finds. The
    container itself survives, so the Ref stays valid and writable after.

    Args:
        ref: the container Ref to empty. Its view must carry
            ``UnsafePrimitiveOpsBase``, and its direct children must all be
            primitives.

    Notes:
        - Declares slot 0 as a mutation position, so ``auto_flow_atomic``
          braces the branch in a Transaction.
        - Unlike ``ScanPrimitivesUnsafe`` it does not absorb a navigation
          failure: a missing address along the Ref's path raises KeyError or
          IndexError.
        - Deletes keys with no descendant cleanup, so a nested container
          that was there loses its own key and leaves its subtree orphaned.
        - Needs a write-capable storage context: run it under a Transaction,
          not a Snapshot.

    Yields:
        Nothing.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Transaction(ClearPrimitivesUnsafeCmd(State.counters)),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            view._unsafe_primitive_clear()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            view._unsafe_primitive_clear()

        return athunk
