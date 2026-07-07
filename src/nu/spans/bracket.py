"""Bracket spans: lifecycle boundaries around a body.

A Bracket is the lifecycle sub-shape of Span (sort BRACKET). It runs the body
inside a scope it opens before and tears down after - a snapshot to read
against, a transaction to commit or roll back. Transparent like every Span: it
forwards the body's yield unchanged (scalar, stream, or nothing).

The core ships two named brackets, ``Snapshot`` and ``Transaction``, as the
model-level shapes. Their lifecycle is a no-op here: a bare core bracket just
runs its body. A fabric subclasses them and overrides the lifecycle to talk to a
real store (see ``nu.virtuals.interactions.atomicity``).

The lifecycle is one method, ``_open`` - a context manager. It opens the
boundary, ``yield``s the scoped context the body runs under, then commits on a
clean exit or rolls back on an exception:

    @contextmanager
    def _open(self, ctx):
        txns = [...open...]               # per-run handles, in the frame
        scoped = ctx.lazy(...)            # scope them into the context
        try:
            yield scoped                  # body runs here
        except BaseException:
            for t in txns: t.abort()      # roll back, then re-raise
            raise
        else:
            for t in txns: t.commit()     # commit

The per-run handles (the open snapshots, the open transactions) live in the
context manager's own frame, captured by closure - never on ``self``. A Term is
immutable and shared across every execution, so it can hold no per-run state
(see ``AUTHORING.md`` - "No per-run or cross-call state"). The boundary is scoped
by swapping ``rt.ctx`` for the body's duration and restoring it after, the same
discipline ``TryCatch`` uses for its isolated handler. For a stream body the
scope spans the drain: it opens when the stream starts and closes (commit /
rollback) when it is exhausted, realizing the body's stream inside the boundary.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.lang import Attr, Bracket, Cardinality


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang.runtime import Context, Runtime


__all__ = ["Snapshot", "Transaction"]


def _guard(rt: Runtime, scope: Callable, body: Callable) -> Iterator:
    """Drive a stream body inside the boundary: the scope spans the whole drain."""
    saved = rt.ctx
    try:
        with scope(saved) as scoped:
            rt.ctx = scoped
            yield from sync_iter(body(rt))
    finally:
        rt.ctx = saved


async def _aguard(rt: Runtime, ascope: Callable, body: Callable) -> AsyncIterator:
    """Async sibling of :func:`_guard`; ``ascope`` is an async context manager."""
    saved = rt.ctx
    try:
        async with ascope(saved) as scoped:
            rt.ctx = scoped
            async for v in aiter_any(await body(rt)):
                yield v
    finally:
        rt.ctx = saved


class _LifecycleBracket(Bracket):
    """Shared lifecycle dispatch for the core brackets.

    Transparent: forwards the body (slot 0) in its own cardinality, running it
    inside ``_open`` (sync run) or ``_aopen`` (async run). The core defaults
    are pass-throughs, so a bare bracket runs its body unchanged; a fabric
    overrides ``_open`` and/or ``_aopen`` to open and close a real store.

    Subclasses that only need sync lifecycle can override ``_open`` alone; the
    default ``_aopen`` wraps it. Subclasses that need genuinely async lifecycle
    (await a subprocess spawn, an RPC, etc.) override ``_aopen`` directly.
    """

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        """Open the boundary (sync), yield the scoped ctx, close on exit.

        Core default: pass-through. Fabrics override to open a snapshot /
        transaction, scope it into the context, commit or roll back.
        """
        yield ctx

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        """Open the boundary (async), yield the scoped ctx, close on exit.

        Core default: delegate to the sync ``_open`` so any subclass overriding
        only ``_open`` works in the async runtime for free. Override this
        directly to await inside setup / teardown.
        """
        with self._open(ctx) as scoped:
            yield scoped

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        scope = self._open

        def thunk(rt: Runtime) -> object:
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, scope, body)
            saved = rt.ctx
            try:
                with scope(saved) as scoped:
                    rt.ctx = scoped
                    return body(rt)
            finally:
                rt.ctx = saved

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        ascope = self._aopen

        async def athunk(rt: Runtime) -> object:
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, ascope, body)
            saved = rt.ctx
            try:
                async with ascope(saved) as scoped:
                    rt.ctx = scoped
                    return await body(rt)
            finally:
                rt.ctx = saved

        return athunk


class Snapshot(_LifecycleBracket):
    """Read-only boundary: snapshot the body's reads, no commit on success.

    Lightweight at the core level - ``_open`` is a pass-through, so a bare
    ``Snapshot(body)`` runs the body unchanged. A fabric-aware Snapshot
    subclasses this and overrides ``_open`` to open and close a real read
    snapshot.
    """


class Transaction(_LifecycleBracket):
    """Atomic boundary: commit the body on success, roll back on failure.

    Lightweight at the core level - ``_open`` is a pass-through, so a bare
    ``Transaction(body)`` runs the body unchanged. A fabric-aware Transaction
    subclasses this and overrides ``_open`` to open a write transaction, commit
    on a clean exit, abort on an exception.
    """
