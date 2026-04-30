"""Control ops for virtuals storage operations.

Atomic: Opens a transaction lazily, provides View on top of it. If the
subtree is pure, auto-selects a snapshot instead.
Snapshot: Opens a read-only snapshot lazily, provides View on top of it.
Transaction: Opens a write transaction lazily, provides View on top of it.

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
from nu.terms.span import Bracket
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu


__all__ = [
    "Atomic",
    "Snapshot",
    "Transaction",
]


def _scope_tags(scope: Hashable | None) -> tuple:
    """Build scope tags for ctx.get / ctx.lazy."""
    return (scope,) if scope is not None else ()


def _wrap_body(children: tuple[Nu, ...]) -> Nu:
    """Pack a variadic body into a single Span body slot."""
    if len(children) == 1:
        return children[0]
    return Sequential(*children)


class Atomic(Bracket):
    """Atomic transaction/snapshot boundary for virtuals operations.

    Before:
      1. Gets Navigator from context (by scope)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (opened via nav.root())

    After:
      - Success: commit transaction (if it was opened)
      - Failure: abort transaction (if it was opened)

    Lazy: if no child accesses storage, no transaction is opened.

    Auto-select: inspects subtree purity. If all terms are pure,
    opens a SnapshotProtocol instead of TransactionProtocol.
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
        self._txn: TransactionProtocol | None = None
        self._snap: SnapshotProtocol | None = None
        self._txns: list[TransactionProtocol] = []
        self._snaps: list[SnapshotProtocol] = []

    def before(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction or snapshot factory.

        If Navigator has predicate bindings (sharding), opens a
        transaction/view per shard with the same predicates.
        """
        self._txns = []
        self._snaps = []

        # Check for sharded navigators
        nav_tags = (self.scope,) if self.scope is not None else ()
        sharded = ctx.get_predicates(Navigator, *nav_tags)

        if sharded:
            return self._enter_sharded(ctx, sharded)

        # Single navigator (common case)
        nav = ctx.get(Navigator, *_scope_tags(self.scope))

        from ..tree.auto_atomic import _has_pv_write

        if _has_pv_write(self):
            return self._enter_transaction(ctx, nav)
        return self._enter_snapshot(ctx, nav)

    def _enter_sharded(self, ctx: Context, sharded: list) -> Context:
        """Open transaction + view per sharded navigator."""
        from ..tree.auto_atomic import _has_pv_write

        scope = self.scope
        child_ctx = ctx
        is_write = _has_pv_write(self)

        for preds, nav in sharded:
            if is_write:
                child_ctx = self._enter_transaction_with_preds(child_ctx, nav, scope, preds)
            else:
                child_ctx = self._enter_snapshot_with_preds(child_ctx, nav, scope, preds)

        return child_ctx

    def _enter_transaction_with_preds(
        self,
        ctx: Context,
        nav: Navigator,
        scope: object,
        preds: dict,
    ) -> Context:
        """Bind lazy txn for one sharded navigator."""

        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            self._txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope), **preds)

    def _enter_snapshot_with_preds(
        self,
        ctx: Context,
        nav: Navigator,
        scope: object,
        preds: dict,
    ) -> Context:
        """Bind lazy snapshot for one sharded navigator."""

        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            self._snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope), **preds)

    def _enter_transaction(self, ctx: Context, nav: Navigator) -> Context:
        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            self._txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope))

    def _enter_snapshot(self, ctx: Context, nav: Navigator) -> Context:
        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            self._snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope))

    def after(self, ctx: Context) -> None:
        """Commit transactions or close snapshots."""
        for txn in self._txns:
            txn.commit()
        for snap in self._snaps:
            snap.close()

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Abort transactions or close snapshots."""
        for txn in self._txns:
            txn.abort()
        for snap in self._snaps:
            snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Atomic({scope_name})"


class Snapshot(_CoreSnapshot):
    """Read-only snapshot boundary for virtuals operations.

    Like Atomic but always opens a snapshot, never a transaction.
    Use when you know the subtree is read-only.
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

    Like Atomic but always opens a transaction, never a snapshot.
    Use when you know the subtree has writes - skips the purity check.
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
