"""``Bracket``: the lifecycle base every bracket subclasses.

A bracket is the lifecycle sub-shape of Span (sort ``BRACKET``, declared by
the ``_Bracket`` kind in ``nu.lang.kinds``). It opens a scope, runs its body
inside it, and closes the scope on exit. Transparent like every Span, it
forwards the body's yield unchanged (scalar, stream, or nothing).

This module is the implementation on top of that kind. The body runs inside
``_open`` / ``_aopen``, context managers that yield the Context the body runs
on. Here they yield the Context unchanged, so a bare ``Bracket(body)`` runs
its body unchanged, and a subclass overrides them to open and close a real
scope (a snapshot, a transaction, a fabric) and yield a Context with what it
provides pushed on top:

    class Txn(nu.Bracket):
        @contextmanager
        def _open(self, ctx, *config):
            txn = begin()                         # per-run, in the frame
            yield ctx.bind(Handle, txn)           # provided for the body
            txn.commit()

The body then runs on a derived Runtime over that Context (``rt.on``). A
context manager that yields nothing (None) leaves the Context as it was.

For a stream body the scope spans the whole drain: it opens when the stream
starts and closes when the stream is exhausted.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Generic, TypeVar

from ._stream import aiter_any, sync_iter
from .attributes import Attr, Cardinality
from .kinds import _Bracket
from .nu import Nu


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator, Sequence

    from nu.lang.runtime import Context, Runtime

V_co = TypeVar("V_co", covariant=True)

__all__ = ["Bracket"]


def _inside(rt: Runtime, ctx: Context | None) -> Runtime:
    """The Runtime the body runs on: ``rt`` over the Context ``_open`` yielded.

    None (a scope that yields nothing) keeps the Context as it was.
    """
    return rt if ctx is None else rt.on(ctx)


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
    with scope(rt.ctx, *config) as ctx:
        yield from sync_iter(body(_inside(rt, ctx)))


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
    async with ascope(rt.ctx, *config) as ctx:
        async for v in aiter_any(await body(_inside(rt, ctx))):
            yield v


class Bracket(_Bracket[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that governs a body's lifecycle: opens a scope, runs the body, closes it.

    Transparent: forwards its one child (the body) in its own cardinality,
    running it inside ``_open`` (sync) or ``_aopen`` (async) on the Context
    they yield. The defaults yield the Context unchanged, so a bare
    ``Bracket(body)`` runs its body unchanged. A bracket is written by
    subclassing this and overriding ``_open`` and/or ``_aopen`` to open and
    close a real scope and yield the Context with what it provides.

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
          config children against the given context the same way and yield
          the Context with what the bracket provides.
        - Nothing is mutated: what a bracket provides is a frame on the
          Context it yields, gone with the body. A task still holding the
          body's Runtime (a delayed task, a stream) keeps it alive.
        - A bracket with no children still compiles (it opens the scope and
          yields nothing); the ``span_has_body`` law is what rejects it.
        - Per-run handles (open snapshots, open transactions) live in the
          context manager's own frame, never on ``self``: a Term is
          immutable and shared across every execution.
    """

    @contextmanager
    def _open(self, ctx: Context, *config: object) -> Iterator[Context]:
        """Open the boundary around the body, yield the body's Context, close it on exit.

        Args:
            ctx: the Context the bracket runs on.
            *config: the values of the config children, in child order.

        Yields:
            The Context the body runs on: ``ctx`` with what the boundary
            provides pushed on top (``ctx.bind`` / ``ctx.lazy``), or ``ctx``
            itself when it provides nothing.

        Notes:
            - The default is a no-op: no lifecycle of its own.
            - An override opens a real scope (a snapshot, a transaction, a
              fabric), yields ``ctx.bind(...)`` / ``ctx.lazy(...)``, then
              closes it on a clean exit or rolls back if the body raises.
        """
        yield ctx

    @asynccontextmanager
    async def _aopen(self, ctx: Context, *config: object) -> AsyncIterator[Context]:
        """Open the boundary around the body, yield the body's Context, close it on exit.

        Args:
            ctx: the Context the bracket runs on.
            *config: the values of the config children, in child order.

        Yields:
            The Context the body runs on, as ``_open`` yields it.

        Notes:
            - The default delegates to the sync ``_open``, so any subclass
              that only overrides ``_open`` works under the async runtime
              for free.
            - Override this directly when setup or teardown itself needs to
              await something (a subprocess spawn, an RPC, etc.).
        """
        with self._open(ctx, *config) as inner:
            yield inner

    # --- the body slot ------------------------------------------------------

    def _inner(self) -> object:
        """The term this bracket runs inside its own layers: its body slot."""
        return self._children[0]

    def _rebody(self, body: object) -> Bracket:
        """A variant of this bracket running ``body``, config children kept.

        How ``With`` stacks brackets into a cascade.
        """
        from nu.lang.literal import Literal

        child = body if isinstance(body, Nu) else Literal(body)
        return self.evolve(children=(child, *self._children[1:]))

    # --- outside a tree -----------------------------------------------------

    def _config_values(self, ctx: Context) -> tuple[object, ...]:
        """Evaluate the config children against ``ctx``, sync.

        Each child is compiled and run on ``ctx`` as a program of its own;
        none is looked into, a Literal runs like any other term.
        """
        from nu.lang.helpers import compile as compile_term
        from nu.lang.helpers.evaluation import eval as eval_program

        return tuple(eval_program(compile_term(c), ctx)[0] for c in self._children[1:])

    async def _aconfig_values(self, ctx: Context) -> tuple[object, ...]:
        """Async sibling of :meth:`_config_values`."""
        from nu.lang.helpers import compile as compile_term
        from nu.lang.helpers.evaluation import aeval

        return tuple([(await aeval(compile_term(c), ctx))[0] for c in self._children[1:]])

    @contextmanager
    def _enter(self, ctx: Context) -> Iterator[Context]:
        """Open this bracket on ``ctx`` outside a tree; its body slot is not run.

        For code that holds a bracket as a spec and runs on what it provides
        (a worker's init, a test).

        Yields:
            The Context with what the bracket provides, live until exit.
        """
        with self._open(ctx, *self._config_values(ctx)) as inner:
            yield ctx if inner is None else inner

    @asynccontextmanager
    async def _aenter(self, ctx: Context) -> AsyncIterator[Context]:
        """Async sibling of :meth:`_enter`."""
        async with self._aopen(ctx, *(await self._aconfig_values(ctx))) as inner:
            yield ctx if inner is None else inner

    # --- compile ------------------------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        scope = self._open

        if not children:
            # No body: open and close the scope, yield nothing. The
            # span_has_body law rejects this shape; compiling it must not.
            def empty_thunk(rt: Runtime) -> None:
                with scope(rt.ctx):
                    return None

            return empty_thunk

        body, config = children[0], children[1:]

        if not config:

            def thunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, scope, body)
                with scope(rt.ctx) as ctx:
                    return body(_inside(rt, ctx))

            return thunk

        def config_thunk(rt: Runtime) -> object:
            values = [c(rt) for c in config]
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, scope, body, values)
            with scope(rt.ctx, *values) as ctx:
                return body(_inside(rt, ctx))

        return config_thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ascope = self._aopen

        if not children:

            async def empty_athunk(rt: Runtime) -> None:
                async with ascope(rt.ctx):
                    return None

            return empty_athunk

        body, config = children[0], children[1:]

        if not config:

            async def athunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, ascope, body)
                async with ascope(rt.ctx) as ctx:
                    return await body(_inside(rt, ctx))

            return athunk

        async def config_athunk(rt: Runtime) -> object:
            values = [await c(rt) for c in config]
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, ascope, body, values)
            async with ascope(rt.ctx, *values) as ctx:
                return await body(_inside(rt, ctx))

        return config_athunk
