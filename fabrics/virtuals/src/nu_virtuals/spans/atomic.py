"""Atomic boundaries for virtuals storage operations.

Snapshot: Opens a read-only snapshot lazily, provides View on top of it.
Transaction: Opens a write transaction lazily, provides View on top of it.
Atomic: Factory that picks Snapshot or Transaction based on the body's
    tracked effects (Transaction if any WRITE, Snapshot otherwise).

Looks up Navigator from context, gets storage from it, and creates
root views via nav.root(). No view_cls parameter needed.

Usage:
    tree = Atomic(
        SetCmd(ref, Lit(42)) >> GetOp(ref),
        scope=UserShape,
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import Context, Mode
from nu.flows.strategy import Sequential
from nu.spans.bracket import Snapshot as _CoreSnapshot
from nu.spans.bracket import Transaction as _CoreTransaction
from nu.terms import Effect, tracked_effects
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu
    from nu.terms.nu import NuBase


__all__ = [
    "Atomic",
    "Snapshot",
    "Transaction",
    "_has_virtuals_write",
]


def _scope_tags(scope: Hashable | None) -> tuple:
    """Build scope tags for ctx.get / ctx.lazy."""
    return (scope,) if scope is not None else ()


def _wrap_body(children: tuple[Nu, ...]) -> Nu:
    """Pack a variadic body into a single Span body slot."""
    if len(children) == 1:
        return children[0]
    return Sequential(*children)


def _has_virtuals_write(node: NuBase) -> bool:
    """Check if subtree has any WRITE effects."""
    return any(eff is Effect.WRITE for _ref, eff in tracked_effects(node))


class Snapshot(_CoreSnapshot):
    """Read-only snapshot boundary for virtuals operations.

    Always opens a snapshot, never a transaction. Use when the subtree
    is read-only.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *children: Nu,
        scope: Hashable | None = None,
    ) -> None:
        super().__init__(_wrap_body(children))
        self.scope = scope
        self._snaps: list[SnapshotProtocol] = []

    def before(self, ctx: Context) -> Context:
        """Scope context: register lazy snapshot factory."""
        self._snaps = []

        nav_tags = (self.scope,) if self.scope is not None else ()
        sharded = ctx.get_predicates(Navigator, *nav_tags)

        if sharded:
            return self._enter_sharded(ctx, sharded)

        nav = ctx.get(Navigator, *_scope_tags(self.scope))
        return self._enter_single(ctx, nav)

    def _enter_sharded(self, ctx: Context, sharded: list) -> Context:
        """Open snapshot + view per sharded navigator."""
        child_ctx = ctx
        for preds, nav in sharded:
            child_ctx = self._enter_single_with_preds(child_ctx, nav, preds)
        return child_ctx

    def _enter_single_with_preds(
        self,
        ctx: Context,
        nav: Navigator,
        preds: dict,
    ) -> Context:
        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            self._snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope), **preds)

    def _enter_single(self, ctx: Context, nav: Navigator) -> Context:
        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            self._snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope))

    def after(self, ctx: Context) -> None:
        """Close snapshots."""
        for snap in self._snaps:
            snap.close()

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Close snapshots."""
        for snap in self._snaps:
            snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Snapshot({scope_name})"


class Transaction(_CoreTransaction):
    """Write transaction boundary for virtuals operations.

    Always opens a transaction, never a snapshot. Use when the subtree
    has writes.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *children: Nu,
        scope: Hashable | None = None,
    ) -> None:
        super().__init__(_wrap_body(children))
        self.scope = scope
        self._txns: list[TransactionProtocol] = []

    def before(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction factory."""
        self._txns = []

        nav_tags = (self.scope,) if self.scope is not None else ()
        sharded = ctx.get_predicates(Navigator, *nav_tags)

        if sharded:
            return self._enter_sharded(ctx, sharded)

        nav = ctx.get(Navigator, *_scope_tags(self.scope))
        return self._enter_single(ctx, nav)

    def _enter_sharded(self, ctx: Context, sharded: list) -> Context:
        """Open transaction + view per sharded navigator."""
        child_ctx = ctx
        for preds, nav in sharded:
            child_ctx = self._enter_single_with_preds(child_ctx, nav, preds)
        return child_ctx

    def _enter_single_with_preds(
        self,
        ctx: Context,
        nav: Navigator,
        preds: dict,
    ) -> Context:
        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            self._txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope), **preds)

    def _enter_single(self, ctx: Context, nav: Navigator) -> Context:
        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            self._txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope))

    def after(self, ctx: Context) -> None:
        """Commit transactions."""
        for txn in self._txns:
            txn.commit()

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Abort transactions."""
        for txn in self._txns:
            txn.abort()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Transaction({scope_name})"


def Atomic(  # noqa: N802 — factory mimics class spelling
    *children: Nu,
    scope: Hashable | None = None,
) -> Snapshot | Transaction:
    """Pick Snapshot or Transaction based on the body's tracked effects.

    Returns a Transaction if any child has a WRITE-effect subtree,
    otherwise a Snapshot. The choice happens at construction time, so
    every Bracket node in the resulting tree has a concrete type.
    """
    body = _wrap_body(children)
    if _has_virtuals_write(body):
        return Transaction(body, scope=scope)
    return Snapshot(body, scope=scope)
