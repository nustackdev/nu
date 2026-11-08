"""One bracket per store a term touches, found from the term's own refs.

``auto_flow_atomic`` places a bracket on each branch of each Flow, so code that
waits never holds one across the wait. ``atomic`` is its compact sibling for
code that does not wait: it brackets the whole term once, as one commit, and
works out which stores to bracket from the refs the term holds, so a program
never names a store.

It reads the term the way ``auto_flow_atomic`` does. A kv ref belongs to the
store its chain is rooted at: the root Shape, which is also the tag its
Navigator is bound under. A ref in a slot its node declares as mutating is a
write, any other ref is a read, and a ref a bracket already in the term covers
does not count. Mem refs (``nu.let``, ``nu.Frame``) are not stores and never
count.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu

from ..errors import BracketError
from ..interactions.atomicity import RetryOnConflict, Snapshot, Transaction
from .auto_flow_atomic import _dominates, _is_dynamic, _iter_uncovered


if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator

    from nu.lang import Nu


__all__ = ["atomic"]


def _stores(term: Nu) -> dict[Hashable | None, bool]:
    """Each store the term touches outside its own brackets, and whether it writes there.

    Keyed by root Shape, in the order the term first touches each one. A ref
    built outside any Shape has no root and counts as the untagged store.
    """
    stores: dict[Hashable | None, bool] = {}
    for ref, wrote in _iter_uncovered(term, None, ()):
        root = ref._root_shape  # type: ignore[attr-defined]
        stores[root] = stores.get(root, False) or wrote
    return stores


def _write_brackets(node: object) -> Iterator[Hashable | None]:
    """The scope of every Transaction already in the term, past dynamic subtrees."""
    if _is_dynamic(node):
        return
    if isinstance(node, Transaction):
        yield node.scope
    for child in nu.tree.children(node):
        yield from _write_brackets(child)


def _name(store: Hashable | None) -> str:
    return "the untagged store" if store is None else getattr(store, "__name__", repr(store))


def atomic(term: Nu) -> Nu:
    """Brackets a term once, on just the stores it touches: one commit, one consistent read.

    The store a term writes gets a ``Transaction``, retried when a concurrent
    writer wins the commit. Each store it only reads gets a ``Snapshot``. So a
    term that writes one store and finds its key in another reads that key
    from a snapshot inside the write, and a term that only reads opens
    snapshots and nothing else. Every write lands together or none does.

    The decision is made here, while the tree is built, and what comes back is
    the term inside ordinary ``Snapshot`` / ``Transaction`` nodes, so every
    later pass sees concrete brackets.

    Args:
        term: the term to bracket. Usually an op or a short run of ops, with
            no wait in it.

    Raises:
        BracketError: at build, when the term writes two stores. One commit
            lands in one store, so two stores are two commits: bracket each
            write on its own. Also when the term holds a write bracket on the
            store it writes outside that bracket, since two transactions on one
            store never join.

    Notes:
        - A store is a root Shape: the one a ref chain starts at, and the tag
          its Navigator is bound under. Two root Shapes are two stores, even
          when both are bound to one untagged Navigator.
        - Only kv refs count. ``nu.let`` and other mem writes do not make a
          term a write.
        - Brackets already in the term are kept, and what they cover does not
          count, so ``atomic(atomic(t))`` is ``atomic(t)``, and an inner
          bracket on another store stays its own commit.
        - A lost commit is retried as ``RetryOnConflict`` does, against fresh
          state, so whatever the term does outside the stores runs again. The
          last conflict is raised.
        - Brackets open on first use, so a store the term only might touch
          costs nothing when it does not.
        - Dynamic subtrees (a program loaded at run time) are opaque: their
          refs are not seen here, so they bracket themselves.
        - Holds its brackets for the whole term. A term that waits (a
          subscription, a sleep, a call out) belongs in ``auto_flow_atomic``,
          which brackets each step instead.

    Yields:
        The term's own value, unchanged.

    Example:
        class Space(nu.Shape):
            cell_keys = nustd.kv.DictRef.slot(str)

        class State(nu.Shape):
            counts = nustd.kv.DictRef.slot(int)

        # writes State, reads the key from a Space snapshot: one State commit
        bump = nustd.kv.atomic(State.counts[Space.cell_keys["summary"]].set(1))
    """
    stores = _stores(term)
    written = [store for store, wrote in stores.items() if wrote]
    if len(written) > 1:
        names = ", ".join(_name(store) for store in written)
        msg = (
            f"atomic: the term writes {len(written)} stores ({names}); one bracket commits "
            "to one store, so bracket each write on its own"
        )
        raise BracketError(msg)
    body = term
    for store, wrote in stores.items():
        if not wrote:
            body = Snapshot(body, scope=store)
    if not written:
        return body
    (store,) = written
    if any(_dominates(scope, store) for scope in _write_brackets(term)):
        msg = (
            f"atomic: the term already holds a write bracket on {_name(store)} and writes "
            "it outside that bracket too; two transactions on one store never join, so "
            "bracket the whole term once"
        )
        raise BracketError(msg)
    return RetryOnConflict(Transaction(body, scope=store))
