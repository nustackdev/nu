"""PV Spans — context-shaping boundaries for PV storage operations.

Atomic: Opens a transaction lazily, provides View on top of it.
Snapshot: Opens a read-only snapshot lazily, provides View on top of it.

Usage:
    tree = Atomic(
        Seq(
            SetCmd(ref, Lit(42)),
            GetOp(ref),
        ),
        scope=UserShape,
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pv.view import View
from tkv.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol

from everybase import Context, Span, Term, find
from everypv.views import DictView


if TYPE_CHECKING:
    from collections.abc import Hashable

    from everybase import Executable


__all__ = [
    "Atomic",
    "Snapshot",
    "Transaction",
]


class Atomic(Span):
    """Atomic transaction boundary for PV operations.

    On enter:
      1. Gets StorageProtocol from context (by scope)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (opened on top of transaction)

    On exit:
      - Success: commit transaction (if it was opened)
      - Failure: abort transaction (if it was opened)

    Lazy: if no child accesses storage, no transaction is opened.

    Auto-select: inspects subtree purity. If all terms are pure,
    opens a SnapshotProtocol instead of TransactionProtocol.
    """

    def __init__(
        self,
        *children: Executable,
        scope: Hashable | None = None,
        view_cls: type[View] = DictView,
    ) -> None:
        """Initialize atomic span.

        Args:
            *children: Child nodes to execute within this boundary.
            scope: Scope for context lookup (any hashable — Shape, table, etc.).
            view_cls: View class to open on top of the storage context.
        """
        super().__init__(*children)
        self.scope = scope
        self.view_cls = view_cls
        self._txn: TransactionProtocol | None = None
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction or snapshot factory."""
        storage = ctx.get(StorageProtocol, scope=self.scope)

        # Check if subtree is pure (all terms are read-only)
        has_impure = any(not t.is_self_pure for t in find(self, lambda n: isinstance(n, Term)))

        if has_impure:
            return self._enter_transaction(ctx, storage)
        return self._enter_snapshot(ctx, storage)

    def _enter_transaction(self, ctx: Context, storage: StorageProtocol) -> Context:
        view_cls = self.view_cls
        scope = self.scope

        def open_txn() -> TransactionProtocol:
            self._txn = storage.begin_transaction()
            return self._txn

        child_ctx = ctx.with_factory(TransactionProtocol, open_txn, scope=scope)

        def open_view() -> View:
            txn = child_ctx.get(TransactionProtocol, scope=scope)
            return view_cls.open_root(txn)

        return child_ctx.with_factory(View, open_view, scope=scope)

    def _enter_snapshot(self, ctx: Context, storage: StorageProtocol) -> Context:
        view_cls = self.view_cls
        scope = self.scope

        def open_snap() -> SnapshotProtocol:
            self._snap = storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.with_factory(SnapshotProtocol, open_snap, scope=scope)

        def open_view() -> View:
            snap = child_ctx.get(SnapshotProtocol, scope=scope)
            return view_cls.open_root(snap)

        return child_ctx.with_factory(View, open_view, scope=scope)

    def exit_success(self, ctx: Context) -> None:
        """Commit transaction or close snapshot if opened."""
        if self._txn is not None:
            self._txn.commit()
        elif self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Abort transaction or close snapshot if opened."""
        if self._txn is not None:
            self._txn.abort()
        elif self._snap is not None:
            self._snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Atomic({scope_name})"


class Snapshot(Span):
    """Read-only snapshot boundary for PV operations.

    Like Atomic but always opens a snapshot, never a transaction.
    Use when you know the subtree is read-only.

    On enter:
      1. Gets StorageProtocol from context (by scope)
      2. Registers lazy factory for SnapshotProtocol
      3. Registers lazy factory for View (opened on top of snapshot)

    On exit:
      - Closes snapshot (if it was opened)
    """

    def __init__(
        self,
        *children: Executable,
        scope: Hashable | None = None,
        view_cls: type[View] = DictView,
    ) -> None:
        """Initialize snapshot span.

        Args:
            *children: Child nodes to execute within this boundary.
            scope: Scope for context lookup (any hashable — Shape, table, etc.).
            view_cls: View class to open on top of the snapshot.
        """
        super().__init__(*children)
        self.scope = scope
        self.view_cls = view_cls
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy snapshot factory."""
        storage = ctx.get(StorageProtocol, scope=self.scope)
        view_cls = self.view_cls
        scope = self.scope

        def open_snap() -> SnapshotProtocol:
            self._snap = storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.with_factory(SnapshotProtocol, open_snap, scope=scope)

        def open_view() -> View:
            snap = child_ctx.get(SnapshotProtocol, scope=scope)
            return view_cls.open_root(snap)

        return child_ctx.with_factory(View, open_view, scope=scope)

    def exit_success(self, ctx: Context) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Snapshot({scope_name})"


class Transaction(Span):
    """Write transaction boundary for PV operations.

    Like Atomic but always opens a transaction, never a snapshot.
    Use when you know the subtree has writes — skips the purity check.

    On enter:
      1. Gets StorageProtocol from context (by scope)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (opened on top of transaction)

    On exit:
      - Success: commit transaction (if it was opened)
      - Failure: abort transaction (if it was opened)
    """

    def __init__(
        self,
        *children: Executable,
        scope: Hashable | None = None,
        view_cls: type[View] = DictView,
    ) -> None:
        super().__init__(*children)
        self.scope = scope
        self.view_cls = view_cls
        self._txn: TransactionProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction factory."""
        storage = ctx.get(StorageProtocol, scope=self.scope)
        view_cls = self.view_cls
        scope = self.scope

        def open_txn() -> TransactionProtocol:
            self._txn = storage.begin_transaction()
            return self._txn

        child_ctx = ctx.with_factory(TransactionProtocol, open_txn, scope=scope)

        def open_view() -> View:
            txn = child_ctx.get(TransactionProtocol, scope=scope)
            return view_cls.open_root(txn)

        return child_ctx.with_factory(View, open_view, scope=scope)

    def exit_success(self, ctx: Context) -> None:
        """Commit transaction if opened."""
        if self._txn is not None:
            self._txn.commit()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Abort transaction if opened."""
        if self._txn is not None:
            self._txn.abort()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Transaction({scope_name})"
