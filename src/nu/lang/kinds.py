"""The Nu kind taxonomy: the user-facing Term classes that declare each sort.

A taxonomy of ``Nu`` subclasses. The leaves (``Ref``, ``ScalarQuery``,
``StreamQuery``, ``Command``, ``ScalarAction``, ``StreamAction``,
``Strategy``, ``Control``, ``Bracket``, ``Policy``) carry the sort and
cardinality bindings concrete nodes use. The interiors (``Interaction``,
``Query``, ``Action``, ``Flow``, ``Span``) are abstract groupings for
``subsort`` queries and for the dispatch surface ``Interaction._eval`` /
``_aeval``.

``Bracket`` is also the lifecycle base every bracket subclasses: it compiles
its body inside ``_open`` / ``_aopen``, context managers that are no-ops here,
so a bare ``Bracket(body)`` runs its body unchanged and a subclass overrides
them to open and close a real scope (a snapshot, a transaction, a fabric).

A reduction is not a kind. A kind says whether a node mutates and what it
gives out; a reduction says what one of its slots takes in: a stream, folded
to whatever the kind gives out. So ``Reduction`` is a mixin that declares
``reduces``, the index of that slot, and each scalar-out kind has its own
reduction base: ``QueryReduction`` reads and yields one value,
``ActionReduction`` writes and yields one value, ``CommandReduction`` writes
and yields nothing. Each keeps its kind's sort, cardinality and composition
rules; the cardinality laws read ``reduces`` to let the stream into that
one slot.

"Kind" is the Python class of a Term (Ref, Interaction, ...); "sort" is the
attribute concern naming the structural category. This module sits on top
of ``nu.lang.nu`` (the base) and ``nu.lang.attributes`` (Sort and
Cardinality value spaces).
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Generic, TypeVar

from nu.engine import Declared

from ._stream import aiter_any, sync_iter
from .attributes import Attr, Cardinality, Sort
from .nu import Nu


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator, Sequence

    from nu.lang.runtime import Context, Runtime

V_co = TypeVar("V_co", covariant=True)

__all__ = [
    "Action",
    "ActionReduction",
    "Bracket",
    "Command",
    "CommandReduction",
    "Control",
    "Flow",
    "Interaction",
    "Policy",
    "Query",
    "QueryReduction",
    "Reduction",
    "Ref",
    "ScalarAction",
    "ScalarQuery",
    "Span",
    "Strategy",
    "StreamAction",
    "StreamQuery",
]


class Ref(Nu[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A name for a location in a Fabric: the abstract Ref kind.

    A Ref is the only atom that touches Context, but it touches it through a
    Fabric, and each Fabric has its own concrete Ref (``Attr`` for the
    Context-attrs fabric, fabric / shape Refs for others). This base is bare:
    it declares only the sort and cardinality every Ref shares and nothing
    else - no name, no read, no write. A bare ``Ref`` is for structural
    analysis; to run, use a concrete fabric Ref.

    A Ref names a location, but the location is never knowable from the base:
    it can be static or computed, and it lives in the concrete fabric Ref, not
    here. What the effect system reads off a Ref is its *fabric*, identified by
    its concrete class, never a location name (which may not exist statically).
    """

    _sort = Declared(value=Sort.REF, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class Interaction(Nu[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a node that interacts with the Context. Never instantiated.

    Concrete sub-kinds implement ``_eval`` / ``_aeval`` to drive execution.
    Both receive the per-execution ``Runtime`` and the node's ``nid`` (its
    integer position in the attributed program); they recurse via
    ``rt.eval(child_nid)`` and reach for ``self._children`` and their own fields
    directly. Attribute reads use ``rt.program.attrs[name][nid]``.
    """

    def _eval(self, rt: Runtime, nid: int) -> V_co:
        """Evaluate this node synchronously; return its value or None."""
        msg = f"{type(self).__name__}._eval is not implemented"
        raise NotImplementedError(msg)

    async def _aeval(self, rt: Runtime, nid: int) -> V_co:
        """Evaluate this node asynchronously; return its value or None."""
        msg = f"{type(self).__name__}._aeval is not implemented"
        raise NotImplementedError(msg)


class Query(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a value-producing Interaction."""


class ScalarQuery(Query[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Query that yields exactly one value."""

    _sort = Declared(value=Sort.SCALAR_QUERY, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class StreamQuery(Query[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Query that yields zero or more values."""

    _sort = Declared(value=Sort.STREAM_QUERY, name="sort")
    _cardinality = Declared(value=Cardinality.STREAM, name="cardinality")


class Command(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A mutating Interaction. Yields nothing; its only sub-shape is scalar."""

    _sort = Declared(value=Sort.SCALAR_COMMAND, name="sort")
    _cardinality = Declared(value=Cardinality.VOID, name="cardinality")


class Action(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a dual-citizen Interaction. Mutates Context and yields a value."""


class ScalarAction(Action[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """An Action that mutates and yields exactly one value."""

    _sort = Declared(value=Sort.SCALAR_ACTION, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


class StreamAction(Action[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """An Action that mutates and yields zero or more values.

    The stream-shaped twin of ScalarAction: one atomic mutate-and-yield-many
    (drain a queue, ``DELETE ... RETURNING`` over a predicate). A scalar
    consumer must reduce it like any StreamQuery; the cardinality law gates
    that off ``cardinality`` alone, with no per-kind special case.
    """

    _sort = Declared(value=Sort.STREAM_ACTION, name="sort")
    _cardinality = Declared(value=Cardinality.STREAM, name="cardinality")


class Flow(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a Command-composing Interaction. Yields nothing."""

    _cardinality = Declared(value=Cardinality.VOID, name="cardinality")


class Strategy(Flow[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Flow that composes Commands directly."""

    _sort = Declared(value=Sort.STRATEGY, name="sort")


class Control(Flow[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Flow that composes Commands under Query parameters."""

    _sort = Declared(value=Sort.CONTROL, name="sort")


class Span(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: a transparent Interaction; yields what its body yields."""

    _cardinality = Declared(value=Cardinality.TRANSPARENT, name="cardinality")


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


class Bracket(Span[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that governs a body's lifecycle: opens a scope, runs the body, closes it.

    Transparent: forwards its one child (the body) in its own cardinality,
    running it inside ``_open`` (sync) or ``_aopen`` (async). The defaults
    are no-ops, so a bare ``Bracket(body)`` runs its body unchanged. A
    bracket is written by subclassing this and overriding ``_open`` and/or
    ``_aopen`` to open and close a real scope.

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
        - A bracket with no children still compiles (it opens the scope and
          yields nothing); the ``span_has_body`` law is what rejects it.
    """

    _sort = Declared(value=Sort.BRACKET, name="sort")

    @contextmanager
    def _open(self, ctx: Context, *config: object) -> Iterator[None]:
        """Open the boundary around the body, close it on exit.

        Args:
            ctx: the task's context; what the boundary opens is provided on
                ``ctx.fabrics`` for as long as the body runs.
            *config: the values of the config children, in child order.

        Notes:
            - The default is a no-op: no lifecycle of its own.
            - An override opens a real scope (a snapshot, a transaction, a
              fabric), provides it with ``ctx.fabrics.bind`` / ``lazy``, then
              closes it on a clean exit or rolls back if the body raises.
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
            - The default delegates to the sync ``_open``, so any subclass
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


class Policy(Span[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """A Span that governs a body's execution on failure."""

    _sort = Declared(value=Sort.POLICY, name="sort")


# --- reductions: a slot role, not a kind -------------------------------------


class Reduction(Interaction[V_co], Generic[V_co]):  # PEP 695 has no variance markers
    """Abstract: an Interaction with one slot that takes a stream and folds it.

    Declares ``reduces``, the index of that slot, 0 by default; a subclass
    moves it by redeclaring ``_reduces``. Carries no sort or cardinality of
    its own: mix it with a scalar-out kind, through ``QueryReduction``,
    ``ActionReduction`` or ``CommandReduction``. Every other slot of the node
    stays scalar.
    """

    _reduces = Declared(value=0, name="reduces")


class QueryReduction(Reduction[V_co], ScalarQuery[V_co]):
    """A ScalarQuery that folds a stream down to one value (``Sum``, ``Collect``)."""


class ActionReduction(Reduction[V_co], ScalarAction[V_co]):
    """A ScalarAction that folds a stream into one write and yields one value.

    A blob store fed a stream of pieces that yields the new id.
    """


class CommandReduction(Reduction[V_co], Command[V_co]):
    """A Command that folds a stream into one write and yields nothing.

    Appending a whole stream to a log in one write.
    """
