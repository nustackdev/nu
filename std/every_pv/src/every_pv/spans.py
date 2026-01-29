"""PV Spans — context-shaping boundaries for PV storage operations.

PVAtomic: Opens a transaction lazily, provides View on top of it.
PVSnapshot: Opens a read-only snapshot lazily, provides View on top of it.

Usage:
    tree = PVAtomic(UserShape, DictView,
        Seq(
            SetCmd(ref, Lit(42)),
            GetOp(ref),
        )
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pv.view import View
from tkv.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol

from everyabc import Context, Span, Term, find


if TYPE_CHECKING:
    from everyabc import Executable


__all__ = [
    "PVAtomic",
    "PVSnapshot",
]


class PVAtomic(Span):
    """Atomic transaction boundary for PV operations.

    On enter:
      1. Gets StorageProtocol from context (by shape)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (opened on top of transaction)

    On exit:
      - Success: commit transaction (if it was opened)
      - Failure: abort transaction (if it was opened)

    Lazy: if no child accesses storage, no transaction is opened.

    Auto-select: inspects subtree purity. If all terms are pure,
    opens a SnapshotProtocol instead of TransactionProtocol.
    """

    def __init__(self, shape: type, view_cls: type[View], *children: Executable) -> None:
        """Initialize atomic span.

        Args:
            shape: Shape class for context lookup (multi-store discrimination).
            view_cls: View class to open on top of the storage context.
            *children: Child nodes to execute within this boundary.
        """
        super().__init__(*children)
        self.shape = shape
        self.view_cls = view_cls
        self._txn: TransactionProtocol | None = None
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction or snapshot factory."""
        storage = ctx.get(StorageProtocol, shape=self.shape)

        # Check if subtree is pure (all terms are read-only)
        has_impure = any(not t.is_self_pure for t in find(self, lambda n: isinstance(n, Term)))

        if has_impure:
            return self._enter_transaction(ctx, storage)
        return self._enter_snapshot(ctx, storage)

    def _enter_transaction(self, ctx: Context, storage: StorageProtocol) -> Context:
        view_cls = self.view_cls
        shape = self.shape

        def open_txn() -> TransactionProtocol:
            self._txn = storage.begin_transaction()
            return self._txn

        child_ctx = ctx.with_factory(TransactionProtocol, open_txn, shape=shape)

        def open_view() -> View:
            txn = child_ctx.get(TransactionProtocol, shape=shape)
            return view_cls.open_root(txn)

        return child_ctx.with_factory(View, open_view, shape=shape)

    def _enter_snapshot(self, ctx: Context, storage: StorageProtocol) -> Context:
        view_cls = self.view_cls
        shape = self.shape

        def open_snap() -> SnapshotProtocol:
            self._snap = storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.with_factory(SnapshotProtocol, open_snap, shape=shape)

        def open_view() -> View:
            snap = child_ctx.get(SnapshotProtocol, shape=shape)
            return view_cls.open_root(snap)

        return child_ctx.with_factory(View, open_view, shape=shape)

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

    def with_children(self, *children: Executable) -> PVAtomic:
        """Return new PVAtomic with replaced children."""
        if children == self._children:
            return self
        return PVAtomic(self.shape, self.view_cls, *children)

    def __repr__(self) -> str:
        return f"PVAtomic({self.shape.__name__})"


class PVSnapshot(Span):
    """Read-only snapshot boundary for PV operations.

    Like PVAtomic but always opens a snapshot, never a transaction.
    Use when you know the subtree is read-only.

    On enter:
      1. Gets StorageProtocol from context (by shape)
      2. Registers lazy factory for SnapshotProtocol
      3. Registers lazy factory for View (opened on top of snapshot)

    On exit:
      - Closes snapshot (if it was opened)
    """

    def __init__(self, shape: type, view_cls: type[View], *children: Executable) -> None:
        """Initialize snapshot span.

        Args:
            shape: Shape class for context lookup (multi-store discrimination).
            view_cls: View class to open on top of the snapshot.
            *children: Child nodes to execute within this boundary.
        """
        super().__init__(*children)
        self.shape = shape
        self.view_cls = view_cls
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy snapshot factory."""
        storage = ctx.get(StorageProtocol, shape=self.shape)
        view_cls = self.view_cls
        shape = self.shape

        def open_snap() -> SnapshotProtocol:
            self._snap = storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.with_factory(SnapshotProtocol, open_snap, shape=shape)

        def open_view() -> View:
            snap = child_ctx.get(SnapshotProtocol, shape=shape)
            return view_cls.open_root(snap)

        return child_ctx.with_factory(View, open_view, shape=shape)

    def exit_success(self, ctx: Context) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def with_children(self, *children: Executable) -> PVSnapshot:
        """Return new PVSnapshot with replaced children."""
        if children == self._children:
            return self
        return PVSnapshot(self.shape, self.view_cls, *children)

    def __repr__(self) -> str:
        return f"PVSnapshot({self.shape.__name__})"
