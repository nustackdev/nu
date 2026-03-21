"""Spans - context-shaping boundaries for virtuals storage operations.

Atomic: Opens a transaction lazily, provides View on top of it.
Snapshot: Opens a read-only snapshot lazily, provides View on top of it.

Spans look up Navigator from context, get storage from it, and create
root views via nav.root(). No view_cls parameter needed.

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

from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol
from virtuals.view import View

from everybase import Context, Span


if TYPE_CHECKING:
    from collections.abc import Hashable

    from everybase import Executable


__all__ = [
    "Atomic",
    "Snapshot",
    "Transaction",
]


def _tags(typ: type, scope: Hashable | None) -> tuple:
    """Build tag tuple from type and optional scope."""
    return (typ, scope) if scope is not None else (typ,)


class Atomic(Span):
    """Atomic transaction boundary for virtuals operations.

    On enter:
      1. Gets Navigator from context (by scope)
      2. Registers lazy factory for TransactionProtocol
      3. Registers lazy factory for View (opened via nav.root())

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
    ) -> None:
        super().__init__(*children)
        self.scope = scope
        self._txn: TransactionProtocol | None = None
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction or snapshot factory."""
        self._txn = None
        self._snap = None
        nav = ctx[_tags(Navigator, self.scope)]

        # Check for PV writes only - other impure terms (ed stores) are irrelevant
        from .meta.auto_atomic import _has_pv_write

        if _has_pv_write(self):
            return self._enter_transaction(ctx, nav)
        return self._enter_snapshot(ctx, nav)

    def _enter_transaction(self, ctx: Context, nav: Navigator) -> Context:
        scope = self.scope
        tags_txn = _tags(TransactionProtocol, scope)
        tags_view = _tags(View, scope)

        def open_txn() -> TransactionProtocol:
            self._txn = nav.storage.begin_transaction()
            return self._txn

        child_ctx = ctx.lazy(open_txn, *tags_txn)

        def open_view() -> View:
            txn = child_ctx[tags_txn]
            return nav.root(txn)

        return child_ctx.lazy(open_view, *tags_view)

    def _enter_snapshot(self, ctx: Context, nav: Navigator) -> Context:
        scope = self.scope
        tags_snap = _tags(SnapshotProtocol, scope)
        tags_view = _tags(View, scope)

        def open_snap() -> SnapshotProtocol:
            self._snap = nav.storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.lazy(open_snap, *tags_snap)

        def open_view() -> View:
            snap = child_ctx[tags_snap]
            return nav.root(snap)

        return child_ctx.lazy(open_view, *tags_view)

    def exit_success(self, ctx: Context) -> None:
        """Commit transaction or close snapshot if opened."""
        if self._txn is not None:
            self._txn.commit()
        elif self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: BaseException) -> None:
        """Abort transaction or close snapshot if opened."""
        if self._txn is not None:
            self._txn.abort()
        elif self._snap is not None:
            self._snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Atomic({scope_name})"


class Snapshot(Span):
    """Read-only snapshot boundary for virtuals operations.

    Like Atomic but always opens a snapshot, never a transaction.
    Use when you know the subtree is read-only.
    """

    def __init__(
        self,
        *children: Executable,
        scope: Hashable | None = None,
    ) -> None:
        super().__init__(*children)
        self.scope = scope
        self._snap: SnapshotProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy snapshot factory."""
        self._snap = None
        nav = ctx[_tags(Navigator, self.scope)]
        scope = self.scope
        tags_snap = _tags(SnapshotProtocol, scope)
        tags_view = _tags(View, scope)

        def open_snap() -> SnapshotProtocol:
            self._snap = nav.storage.begin_snapshot()
            return self._snap

        child_ctx = ctx.lazy(open_snap, *tags_snap)

        def open_view() -> View:
            snap = child_ctx[tags_snap]
            return nav.root(snap)

        return child_ctx.lazy(open_view, *tags_view)

    def exit_success(self, ctx: Context) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def exit_failure(self, ctx: Context, error: BaseException) -> None:
        """Close snapshot if opened."""
        if self._snap is not None:
            self._snap.close()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Snapshot({scope_name})"


class Transaction(Span):
    """Write transaction boundary for virtuals operations.

    Like Atomic but always opens a transaction, never a snapshot.
    Use when you know the subtree has writes - skips the purity check.
    """

    def __init__(
        self,
        *children: Executable,
        scope: Hashable | None = None,
    ) -> None:
        super().__init__(*children)
        self.scope = scope
        self._txn: TransactionProtocol | None = None

    def enter(self, ctx: Context) -> Context:
        """Scope context: register lazy transaction factory."""
        self._txn = None
        nav = ctx[_tags(Navigator, self.scope)]
        scope = self.scope
        tags_txn = _tags(TransactionProtocol, scope)
        tags_view = _tags(View, scope)

        def open_txn() -> TransactionProtocol:
            self._txn = nav.storage.begin_transaction()
            return self._txn

        child_ctx = ctx.lazy(open_txn, *tags_txn)

        def open_view() -> View:
            txn = child_ctx[tags_txn]
            return nav.root(txn)

        return child_ctx.lazy(open_view, *tags_view)

    def exit_success(self, ctx: Context) -> None:
        """Commit transaction if opened."""
        if self._txn is not None:
            self._txn.commit()

    def exit_failure(self, ctx: Context, error: BaseException) -> None:
        """Abort transaction if opened."""
        if self._txn is not None:
            self._txn.abort()

    def __repr__(self) -> str:
        scope_name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Transaction({scope_name})"
