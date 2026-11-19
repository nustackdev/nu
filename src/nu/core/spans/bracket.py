"""Bracket spans: lifecycle boundaries around a body.

A Bracket is the lifecycle sub-shape of Span (sort BRACKET). It runs the body
inside a scope it opens before and tears down after, a snapshot to read
against, a transaction to commit or roll back. Transparent like every Span, it
forwards the body's yield unchanged (scalar, stream, or nothing).

The core ships two named brackets, ``Snapshot`` and ``Transaction``, as the
model-level shapes. Their lifecycle is a no-op here: a bare core bracket just
runs its body. A fabric subclasses them and overrides the lifecycle to talk to a
real store (see ``nustd.kv.interactions.atomicity``).

The lifecycle is one method, ``_open`` - a context manager. It opens the
boundary, provides what it opened on the task's own fabrics store for the
body, then commits on a clean exit or rolls back on an exception:

    @contextmanager
    def _open(self, ctx, *config):
        txns = [...open...]                           # per-run handles, in the frame
        try:
            with ctx.fabrics.lazy(Txn, open_txn):     # provided for the body
                yield                                 # body runs here
        except BaseException:
            for t in txns: t.abort()                  # roll back, then re-raise
            raise
        else:
            for t in txns: t.commit()                 # commit

The per-run handles (the open snapshots, the open transactions) live in the
context manager's own frame, captured by closure - never on ``self``. A Term is
immutable and shared across every execution, so it can hold no per-run state
(see ``AUTHORING.md`` - "No per-run or cross-call state"). The Context is never
replaced: the scope lives in the store and ends with the ``with``. For a stream
body the scope spans the drain: it opens when the stream starts and closes
(commit / rollback) when it is exhausted, realizing the body's stream inside
the boundary.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.lang import Attr, Bracket, Cardinality


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator, Sequence

    from nu.lang.runtime import Context, Runtime


__all__ = ["Snapshot", "Transaction"]


def _guard(rt: Runtime, scope: Callable, body: Callable, config: Sequence[object] = ()) -> Iterator:
    """Run a stream body inside the boundary, spanning the whole drain.

    Args:
        rt: the runtime the body executes under.
        scope: the sync context manager (``_open``) that opens and closes
            the boundary.
        body: the compiled body thunk.
        config: the bracket's config values, already evaluated.

    Yields:
        The body's stream, one item at a time, with the boundary still open
        around the whole drain.
    """
    with scope(rt.ctx, *config):
        yield from sync_iter(body(rt))


async def _aguard(
    rt: Runtime, ascope: Callable, body: Callable, config: Sequence[object] = ()
) -> AsyncIterator:
    """Async sibling of :func:`_guard`; ``ascope`` is an async context manager.

    Args:
        rt: the runtime the body executes under.
        ascope: the async context manager (``_aopen``) that opens and
            closes the boundary.
        body: the compiled async body thunk.
        config: the bracket's config values, already evaluated.

    Yields:
        The body's stream, one item at a time, with the boundary still open
        around the whole drain.
    """
    async with ascope(rt.ctx, *config):
        async for v in aiter_any(await body(rt)):
            yield v


class _LifecycleBracket(Bracket):
    """Shared lifecycle dispatch the core brackets subclass.

    Transparent: forwards its one child (the body) in its own cardinality,
    running it inside ``_open`` (sync) or ``_aopen`` (async). The core
    defaults are pass-throughs, so a bare bracket runs its body unchanged. A
    fabric overrides ``_open`` and/or ``_aopen`` to open and close a real
    store.

    Notes:
        - Overriding ``_open`` alone is enough for sync lifecycle: the
          default ``_aopen`` wraps it, so the subclass gets the async
          runtime for free.
        - Genuinely async lifecycle (awaiting a subprocess spawn, an RPC,
          etc.) means overriding ``_aopen`` directly instead.
        - Children are ``[body, *config]``. The thunk evaluates the config
          children on entry and passes their values to ``_open`` /
          ``_aopen`` after ``ctx``, in child order. A subclass declares
          them as named parameters (``_open(self, ctx, cls, kwargs)``).
        - Outside a tree (a worker opening its init spec, a test) the
          bracket opens through ``_enter`` / ``_aenter``, which evaluate the
          config children against the given context the same way.
    """

    @contextmanager
    def _open(self, ctx: Context, *config: object) -> Iterator[None]:
        """Open the boundary around the body, close it on exit.

        Args:
            ctx: the task's context; what the boundary opens is provided on
                ``ctx.fabrics`` for as long as the body runs.
            *config: the values of the config children, in child order.

        Notes:
            - Core default is a pass-through: no lifecycle of its own.
            - A fabric override opens a real snapshot or transaction, provides
              it with ``ctx.fabrics.bind`` / ``lazy``, then commits on a clean
              exit or rolls back if the body raises.
        """
        yield

    @asynccontextmanager
    async def _aopen(self, ctx: Context, *config: object) -> AsyncIterator[None]:
        """Open the boundary around the body, close it on exit.

        Args:
            ctx: the task's context; what the boundary opens is provided on
                ``ctx.fabrics`` for as long as the body runs.
            *config: the values of the config children, in child order.

        Notes:
            - Core default delegates to the sync ``_open``, so any subclass
              that only overrides ``_open`` works under the async runtime
              for free.
            - Override this directly when setup or teardown itself needs to
              await something (a subprocess spawn, an RPC, etc.).
        """
        with self._open(ctx, *config):
            yield

    # --- the body slot ------------------------------------------------------

    def _inner(self) -> object:
        """The term this bracket runs inside its own layers: its body slot."""
        return self._children[0]

    def _rebody(self, body: object) -> _LifecycleBracket:
        """A variant of this bracket running ``body``, config children kept.

        How ``With`` stacks brackets into a cascade.
        """
        from nu.lang.literal import Literal
        from nu.lang.nu import Nu

        child = body if isinstance(body, Nu) else Literal(body)
        return self.evolve(children=(child, *self._children[1:]))

    # --- outside a tree -----------------------------------------------------

    def _config_values(self, ctx: Context) -> tuple[object, ...]:
        """Evaluate the config children against ``ctx``, sync.

        A Literal gives its value directly; any other child is compiled and
        run on ``ctx`` as a program of its own.
        """
        from nu.lang.helpers import compile as compile_term
        from nu.lang.helpers.evaluation import eval as eval_program
        from nu.lang.literal import Literal

        return tuple(
            c.value if isinstance(c, Literal) else eval_program(compile_term(c), ctx)[0]
            for c in self._children[1:]
        )

    async def _aconfig_values(self, ctx: Context) -> tuple[object, ...]:
        """Async sibling of :meth:`_config_values`."""
        from nu.lang.helpers import compile as compile_term
        from nu.lang.helpers.evaluation import aeval
        from nu.lang.literal import Literal

        values = []
        for c in self._children[1:]:
            values.append(
                c.value if isinstance(c, Literal) else (await aeval(compile_term(c), ctx))[0]
            )
        return tuple(values)

    @contextmanager
    def _enter(self, ctx: Context) -> Iterator[None]:
        """Open this bracket on ``ctx`` outside a tree; its body slot is not run.

        For code that holds a bracket as a spec and keeps what it provides
        live on a context of its own (a worker's init, a test).
        """
        with self._open(ctx, *self._config_values(ctx)):
            yield

    @asynccontextmanager
    async def _aenter(self, ctx: Context) -> AsyncIterator[None]:
        """Async sibling of :meth:`_enter`."""
        async with self._aopen(ctx, *(await self._aconfig_values(ctx))):
            yield

    # --- compile ------------------------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, config = children[0], children[1:]
        scope = self._open

        if not config:

            def thunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, scope, body)
                with scope(rt.ctx):
                    return body(rt)

            return thunk

        def config_thunk(rt: Runtime) -> object:
            values = [c(rt) for c in config]
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, scope, body, values)
            with scope(rt.ctx, *values):
                return body(rt)

        return config_thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, config = children[0], children[1:]
        ascope = self._aopen

        if not config:

            async def athunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, ascope, body)
                async with ascope(rt.ctx):
                    return await body(rt)

            return athunk

        async def config_athunk(rt: Runtime) -> object:
            values = [await c(rt) for c in config]
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, ascope, body, values)
            async with ascope(rt.ctx, *values):
                return await body(rt)

        return config_athunk


class Snapshot(_LifecycleBracket):
    """Read-only boundary around a body: snapshots its reads, nothing to commit.

    At the core level ``_open`` is a pass-through, so a bare
    ``Snapshot(body)`` runs the body unchanged. A fabric-aware Snapshot
    subclasses this and overrides ``_open`` to open a real read snapshot and
    close it after, giving the body a consistent view to read against.

    Args:
        body: the interaction to run inside the boundary.

    Yields:
        The body's own yield, unchanged. A core Snapshot adds no lifecycle
        of its own; only a fabric's override does.

    Example:
        >>> nu.run(nu.Snapshot(nu.Add(1, 2)))[0]
        3
    """


class Transaction(_LifecycleBracket):
    """Atomic boundary around a body: commits on success, rolls back on failure.

    At the core level ``_open`` is a pass-through, so a bare
    ``Transaction(body)`` runs the body unchanged. A fabric-aware
    Transaction subclasses this and overrides ``_open`` to open a real
    write transaction, committing it on a clean exit and aborting it if the
    body raises.

    Args:
        body: the interaction to run inside the boundary.

    Yields:
        The body's own yield, unchanged. A core Transaction adds no
        lifecycle of its own; only a fabric's override does.

    Example:
        >>> nu.run(nu.Transaction(nu.Add(1, 2)))[0]
        3
    """
