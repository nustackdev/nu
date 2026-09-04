"""Atomic boundaries over KV storage, and the retry that makes them survivable.

The core ``Snapshot`` and ``Transaction`` brackets are shape only: they mark a
region of the tree and run the body unchanged. The versions here fill that
shape in against real storage. Each overrides one lifecycle method, ``_open``,
written as a ``@contextmanager``: it finds the Navigator on the ctx, binds a
handle under it, hands the scoped ctx to the body, and tears the handle down
on the way out.

Binding is lazy, through ``ctx.lazy``. A bracket that wraps a body which turns
out never to touch storage opens nothing, so wrapping generously costs nothing.
That is what makes ``auto_flow_atomic`` safe to run over a whole tree.

The open handles live in the contextmanager's frame, captured by closure. They
are never put on ``self``, because a Term is immutable and one instance is
shared across every execution of the program that holds it.

``scope`` is a plain data attribute, not part of the lifecycle: a shape tag
that says which Navigator this boundary is for. In a sharded setup, several
Navigators sit on the ctx under different tags, and the tag routes the bracket
to the right one. It also rides the atom's payload rather than an instance
attribute, so a tree rewrite carries it through.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.core.flows.strategy import Sequential
from nu.core.spans import Retry
from nu.core.spans import Snapshot as _CoreSnapshot
from nu.core.spans import Transaction as _CoreTransaction
from nu.lang import Attr, Cardinality
from virtuals import Navigator
from virtuals.tkv.storage import (
    SnapshotProtocol,
    StorageLockTimeoutError,
    StorageTransactionConflictError,
    TransactionProtocol,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Hashable, Iterator

    from nu.lang import FloatArg, IntArg, Nu
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
    attrs = getattr(type(node), "_attributes", None)
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
        children = getattr(cur, "_children", ())
        stack.extend(c for c in children if hasattr(c, "_children"))
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
    body. ``scope`` is a plain data attribute (the shape tag), living alongside
    the core bracket's ``_open`` lifecycle method. This mixin overrides
    ``compile`` / ``acompile`` to call ``self._open`` directly.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
    """Gives its body one consistent read view of storage, and closes it after.

    Every read inside sees storage as it stood when the snapshot opened, so a
    body reading the same key twice gets the same answer both times even if a
    concurrent writer moved it in between. Nothing is committed on the way out;
    there is nothing to commit.

    Args:
        *children: the body. Several are run in order as one Sequential.
        scope: which Navigator to snapshot, by shape tag. None means the
            untagged one, which is the whole story unless storage is sharded.

    Notes:
        - The snapshot opens on first read, not on entry, so a body that
          never touches storage opens nothing.
        - Under a stream body the boundary spans the whole drain, not just
          the call that builds the stream, so the consumer still reads
          against a live snapshot.
        - With several Navigators bound under the same tag, one snapshot is
          opened per Navigator and all of them close on exit.
        - Binds no write handle, so a mutating op placed inside has no
          transaction of its own to write through.

    Yields:
        The body's own value, unchanged.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=Snapshot(State.counters["hits"], State.counters["misses"]),
        )
    """

    def __init__(self, *children: Nu, scope: Hashable | None = None) -> None:
        super().__init__(_wrap_body(children))
        # Carry the scope tag in payload so Term._with_children (used by the
        # bottom-up rewrite in auto_flow_atomic) preserves it across rebuilds.
        # An instance attribute on the base scope-property path would break
        # payload propagation; keeping it in payload lets rewrites carry it
        # cleanly (see `_LifecycleBracket._open` for the lifecycle method).
        self._payload = {"scope": scope}

    @property
    def scope(self) -> Hashable | None:
        """Shape tag for atomic routing."""
        return self._payload["scope"]

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

    def _scope_lazy(self, ctx: Context, nav: Navigator, snaps: list, preds: dict) -> Context:
        def open_snap() -> SnapshotProtocol:
            snap = nav.storage.begin_snapshot()
            snaps.append(snap)
            return snap

        return ctx.lazy(SnapshotProtocol, open_snap, *_scope_tags(self.scope), **preds)


class Transaction(_VirtualsBracketMixin, _CoreTransaction):
    """Runs its body inside a write transaction: all of it lands, or none of it.

    Writes buffer in the transaction and become visible to everyone else at
    the commit, which happens when the body finishes cleanly. Anything raised
    out of the body aborts instead, and the exception carries on up, so a
    half-applied write is not a state the rest of the program can observe.
    Reads inside see the transaction's own pending writes.

    Args:
        *children: the body. Several are run in order as one Sequential.
        scope: which Navigator to open the transaction against, by shape
            tag. None means the untagged one.

    Notes:
        - The transaction opens on first use, not on entry, so a body that
          never touches storage opens nothing and commits nothing.
        - Under a stream body the boundary spans the whole drain, so the
          commit waits for the consumer to finish rather than firing when
          the stream is built.
        - Aborts on any BaseException, including cancellation, not only on
          Exception.
        - With several Navigators bound under the same tag, one transaction
          is opened per Navigator and each commits on its own. Atomicity is
          per storage, not across them.
        - Committing can lose to a concurrent writer. Wrap in
          ``RetryOnConflict`` where that is expected.

    Yields:
        The body's own value, unchanged.

    Example:
        class State(nu.Shape):
            hits = nu.kv.IntRef.slot()

        app = nu.With(
            nu.kv.memory_navigator(),
            body=RetryOnConflict(Transaction(State.hits.inc())),
        )
    """

    def __init__(self, *children: Nu, scope: Hashable | None = None) -> None:
        super().__init__(_wrap_body(children))
        # See Snapshot.__init__ for why scope lives in payload, not on self.
        self._payload = {"scope": scope}

    @property
    def scope(self) -> Hashable | None:
        """Shape tag for atomic routing."""
        return self._payload["scope"]

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

    def _scope_lazy(self, ctx: Context, nav: Navigator, txns: list, preds: dict) -> Context:
        def open_txn() -> TransactionProtocol:
            txn = nav.storage.begin_transaction()
            txns.append(txn)
            return txn

        return ctx.lazy(TransactionProtocol, open_txn, *_scope_tags(self.scope), **preds)


def Atomic(  # noqa: N802 (factory mimics class spelling)
    *children: Nu,
    scope: Hashable | None = None,
) -> Snapshot | Transaction:
    """Brackets a body with whichever boundary its own writes call for.

    Saves the caller from having to know whether a branch mutates. It scans
    the body for any node declaring a mutation position and returns a
    Transaction if it finds one, a Snapshot if it does not.

    The decision is made here, while the tree is being built, so what ends up
    in the tree is an ordinary ``Snapshot`` or ``Transaction`` node and every
    later pass sees a concrete type rather than a choice still to be made.

    Args:
        *children: the body. Several are run in order as one Sequential.
        scope: the shape tag handed to whichever bracket is chosen.

    Notes:
        - Spelled like a class because it stands in for one at every call
          site; it is a function and cannot be subclassed or matched on.
        - The scan reads declared mutation positions off the node classes,
          so it sees only writes already present in the tree at build time.
        - It descends through everything, brackets included, so a write
          already covered by a nested Transaction still counts.
        - For a whole tree rather than one body, ``auto_flow_atomic`` makes
          the same decision per Flow branch.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=Atomic(State.hits.inc()),  # a Transaction
        )
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
    """Re-runs its body when a storage transaction loses a race, and only then.

    Under concurrent writers a transaction that touches a hot key can fail to
    commit, or time out waiting for a lock. Neither is a real error: the work
    is still valid, it just needs doing again against fresh state. This is
    ``Retry`` with exactly those two failures selected, so everything else -
    a bug, a bad value, a missing key - still surfaces on the first try
    instead of being run four more times.

    Wrap it around the Transaction, not inside it. The retry has to re-enter
    the boundary for the second attempt to see the state that beat it.

    Args:
        body: the Term to re-run. Normally a Transaction.

    Notes:
        - Takes ``Retry``'s keyword-only tuning as well - ``max_attempts``,
          ``delay``, ``backoff``, ``jitter``, ``errors``, and the
          ``on_attempt_fail`` / ``on_success`` / ``on_fail`` hooks - with
          the same meanings.
        - The defaults differ from ``Retry``'s: five attempts rather than
          three, and a real delay with backoff and jitter, because they are
          set for hot-key contention rather than for a generic failure. The
          jitter is what stops a set of contending writers retrying in
          lockstep.
        - Passing ``errors`` replaces the conflict set entirely, so use it
          only to widen or narrow what counts as retryable.
        - Only the async path honours delay, backoff, jitter and the hooks.
          A sync run retries immediately.
        - Exhausting the attempts re-raises the last conflict, so a caller
          that must not fail needs its own ceiling above this one.

    Yields:
        The body's value from the attempt that commits.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=RetryOnConflict(
                Transaction(State.hits.inc()),
                max_attempts=20,
            ),
        )
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
