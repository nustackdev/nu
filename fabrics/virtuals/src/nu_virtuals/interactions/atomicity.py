"""Atomic boundaries + conflict-aware retry for virtuals storage.

Snapshot: opens a read-only snapshot lazily, scopes it into the ctx, closes on exit.
Transaction: opens a write transaction lazily, commits on clean exit, aborts on error.
Atomic: factory that picks Snapshot or Transaction based on the body's tracked
    writes (Transaction if any mutating op, Snapshot otherwise).
RetryOnConflict: Retry preset scoped to the virtuals storage conflict errors.

These subclass the v2 core brackets and override the lifecycle as a single
``@contextmanager`` (``_open``). The per-run handles (open snapshots /
transactions) live in the context-manager frame, captured by closure — never on
``self`` (a Term is immutable and shared across executions). The ``scope`` data
attribute is the shape tag used for predicate routing / multi-navigator setups
(read by ``auto_atomic`` and the structural tests), NOT the lifecycle method.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.flows.strategy import Sequential
from nu.lang import Attr, Cardinality
from nu.spans import Retry
from nu.spans import Snapshot as _CoreSnapshot
from nu.spans import Transaction as _CoreTransaction
from virtuals import Navigator
from virtuals.tkv.storage import (
    SnapshotProtocol,
    StorageLockTimeoutError,
    StorageTransactionConflictError,
    TransactionProtocol,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Hashable, Iterator

    from nu import FloatArg, IntArg, Nu
    from nu.lang.runtime import Context, Runtime


__all__ = [
    "CONFLICT_ERRORS",
    "Atomic",
    "RetryOnConflict",
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


def _node_write_positions(node: object) -> frozenset[int]:
    """Declared write positions on a node via its ``mutates`` attribute, or empty."""
    attrs = getattr(type(node), "attributes", None)
    if not attrs or "mutates" not in attrs:
        return frozenset()
    value = attrs["mutates"].value
    return value if isinstance(value, frozenset) else frozenset(value)


def _has_virtuals_write(node: object) -> bool:
    """Check if the subtree rooted at ``node`` has any declared write position."""
    stack = [node]
    while stack:
        cur = stack.pop()
        if _node_write_positions(cur):
            return True
        children = getattr(cur, "children", ())
        stack.extend(c for c in children if hasattr(c, "children"))
    return False


def _guard(rt: Runtime, opener: Callable, body: Callable) -> Iterator:
    """Drive a stream body inside the boundary: the scope spans the whole drain."""
    saved = rt.ctx
    try:
        with opener(saved) as scoped:
            rt.ctx = scoped
            yield from sync_iter(body(rt))
    finally:
        rt.ctx = saved


async def _aguard(rt: Runtime, opener: Callable, body: Callable) -> AsyncIterator:
    """Async sibling of :func:`_guard`."""
    saved = rt.ctx
    try:
        with opener(saved) as scoped:
            rt.ctx = scoped
            async for v in aiter_any(await body(rt)):
                yield v
    finally:
        rt.ctx = saved


class _VirtualsBracketMixin:
    """Shared lifecycle dispatch: run the body inside ``_open`` (a contextmanager).

    ``_open`` is the fabric lifecycle; subclasses fill in the open/commit/abort
    body. ``scope`` is a plain data attribute (the shape tag), so it does not
    clash with the core bracket's ``scope`` lifecycle method — this mixin
    overrides ``compile`` / ``acompile`` to call ``self._open`` directly.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        opener = self._open

        def thunk(rt: Runtime) -> object:
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, opener, body)
            saved = rt.ctx
            try:
                with opener(saved) as scoped:
                    rt.ctx = scoped
                    return body(rt)
            finally:
                rt.ctx = saved

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        opener = self._open

        async def athunk(rt: Runtime) -> object:
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, opener, body)
            saved = rt.ctx
            try:
                with opener(saved) as scoped:
                    rt.ctx = scoped
                    return await body(rt)
            finally:
                rt.ctx = saved

        return athunk

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:  # pragma: no cover - overridden
        yield ctx


class Snapshot(_VirtualsBracketMixin, _CoreSnapshot):
    """Read-only snapshot boundary for virtuals operations."""

    def __init__(self, *children: Nu, scope: Hashable | None = None) -> None:
        super().__init__(_wrap_body(children))
        self.scope = scope

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        """Open a snapshot lazily, scope it into the ctx, close on exit."""
        snaps: list[SnapshotProtocol] = []
        nav_tags = _scope_tags(self.scope)
        sharded = ctx.get_predicates(Navigator, *nav_tags)

        if sharded:
            child_ctx = ctx
            for preds, nav in sharded:
                child_ctx = self._scope_lazy(child_ctx, nav, snaps, preds)
            scoped = child_ctx
        else:
            nav = ctx.get(Navigator, *nav_tags)
            scoped = self._scope_lazy(ctx, nav, snaps, {})

        try:
            yield scoped
        finally:
            for snap in snaps:
                snap.close()

    def _scope_lazy(
        self, ctx: Context, nav: Navigator, snaps: list, preds: dict
    ) -> Context:
        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope), **preds)

    def __repr__(self) -> str:
        name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Snapshot({name})"


class Transaction(_VirtualsBracketMixin, _CoreTransaction):
    """Write transaction boundary for virtuals operations."""

    def __init__(self, *children: Nu, scope: Hashable | None = None) -> None:
        super().__init__(_wrap_body(children))
        self.scope = scope

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        """Open a transaction lazily, commit on clean exit, abort on error."""
        txns: list[TransactionProtocol] = []
        nav_tags = _scope_tags(self.scope)
        sharded = ctx.get_predicates(Navigator, *nav_tags)

        if sharded:
            child_ctx = ctx
            for preds, nav in sharded:
                child_ctx = self._scope_lazy(child_ctx, nav, txns, preds)
            scoped = child_ctx
        else:
            nav = ctx.get(Navigator, *nav_tags)
            scoped = self._scope_lazy(ctx, nav, txns, {})

        try:
            yield scoped
        except BaseException:
            for txn in txns:
                txn.abort()
            raise
        else:
            for txn in txns:
                txn.commit()

    def _scope_lazy(
        self, ctx: Context, nav: Navigator, txns: list, preds: dict
    ) -> Context:
        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope), **preds)

    def __repr__(self) -> str:
        name = self.scope.__name__ if hasattr(self.scope, "__name__") else str(self.scope)
        return f"Transaction({name})"


def Atomic(  # noqa: N802 — factory mimics class spelling
    *children: Nu,
    scope: Hashable | None = None,
) -> Snapshot | Transaction:
    """Pick Snapshot or Transaction based on the body's tracked writes.

    Returns a Transaction if any child has a mutating op in its subtree,
    otherwise a Snapshot. The choice happens at construction time, so every
    Bracket node in the resulting tree has a concrete type.
    """
    body = _wrap_body(children)
    if _has_virtuals_write(body):
        return Transaction(body, scope=scope)
    return Snapshot(body, scope=scope)


# =============================================================================
# RETRY ON CONFLICT
# =============================================================================


CONFLICT_ERRORS: tuple[type[Exception], ...] = (
    StorageTransactionConflictError,
    StorageLockTimeoutError,
)


class RetryOnConflict(Retry):
    """Retry preset for virtuals storage conflicts.

    Targets ``StorageTransactionConflictError`` and ``StorageLockTimeoutError``
    only — non-conflict exceptions propagate immediately. Defaults are tuned for
    hot-key contention under N concurrent writers. Override any kwarg to tune.
    """

    def __init__(
        self,
        body: Nu,
        *,
        max_attempts: IntArg = 5,
        delay: FloatArg = 0.1,
        backoff: FloatArg = 2.0,
        jitter: FloatArg = 0.5,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
        on_attempt_fail: Nu | None = None,
        on_success: Nu | None = None,
        on_fail: Nu | None = None,
    ) -> None:
        super().__init__(
            body,
            max_attempts=max_attempts,
            delay=delay,
            backoff=backoff,
            jitter=jitter,
            errors=CONFLICT_ERRORS if errors is None else errors,
            on_attempt_fail=on_attempt_fail,
            on_success=on_success,
            on_fail=on_fail,
        )
