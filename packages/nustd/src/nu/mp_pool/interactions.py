"""The interactions of the ``nu.mp_pool`` fabric.

Seven atoms over one ``WorkerPool``: ``Launch``, ``Dispatch``, ``Teleport``,
``Kill``, ``Alive``, ``Running``, ``Workers``. Because the fabric spans many
processes, these are declarative statements about its contents rather than
imperative escapes - the same way ``SetCmd`` is a statement about the attrs
fabric.

**No caller value is payload.** Every worker id, every pool address and the
``init`` override are children, so any of them can come from a ``Ref``, an
``AttrRef`` or any query. ``nu.mp.Teleport`` keeps its target in
``self._payload``, which pins it at construction time; that is the mistake
this fabric exists not to repeat.

The one thing that *is* payload is ``Dispatch``'s body, and it is payload for
a structural reason, not a shortcut. See the warning on that class: a body in
payload is not part of the tree, so no walker reaches it.

Slot order, which is what the laws read:

==========  =========================  ============  ====================
atom        slots                      sort          mutates
==========  =========================  ============  ====================
Launch      (pool, init)               ScalarAction  {0}
Dispatch    (pool, worker)             Command       {0}
Teleport    (body, pool, worker)       Policy        -
Kill        (pool, worker)             Command       {0}
Alive       (pool, worker)             ScalarQuery   -
Running     (pool, worker)             ScalarQuery   -
Workers     (pool,)                    StreamQuery   -
==========  =========================  ============  ====================

``Dispatch`` carries its body in ``_payload["body"]``; ``Teleport`` carries
its body as ``children[0]``. The asymmetry is intended:

- ``Dispatch`` and ``Kill`` are VOID mutators, so ``ref_slots`` requires the
  mutation slot to hold a Ref. The pool ref is slot 0 in both.
- A Command's composition row holds value-yielding children only, and a
  resident body is typically a Flow (``ForeverDo``, ``ReactForever``). A Flow
  in a Command's slot does not compose, so ``Dispatch``'s body cannot be a
  child at all while ``Dispatch`` is a Command - hence the payload.
- ``Teleport`` is a Span, and Span transparency resolves both sort and
  cardinality from ``children[0]``. Its body therefore *has* to be slot 0 or
  the node would present itself to its parent as a scalar ref. The
  constructor signature still reads ``Teleport(pool, body, worker)``; only
  the child order differs.

.. warning::

   A ``Dispatch`` body is not part of the tree it sits in. Tree walkers,
   rewrites, analyses and renders all traverse ``_children``, and payload is
   opaque to every one of them, so a dispatched body is silently skipped by
   whatever pass runs over the enclosing tree. Any pass the body needs must
   be applied by the caller, to the body, before the ``Dispatch`` is built.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import (
    Attr,
    Cardinality,
    Command,
    Literal,
    Nu,
    Policy,
    ScalarAction,
    ScalarQuery,
    StreamQuery,
)
from nu.lang.sentinels import EMPTY, INVALID

from .refs import PoolRef
from .resources import WorkerPool


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Runtime


__all__ = [
    "Alive",
    "Dispatch",
    "Kill",
    "Launch",
    "Running",
    "Teleport",
    "Workers",
]


# --- child helpers ----------------------------------------------------------


def _pool_node(pool: Nu | None) -> Nu:
    """The pool slot: whatever was passed, or the untagged ``PoolRef``."""
    return PoolRef() if pool is None else pool


def _init_node(init: object) -> Nu:
    """The init slot: a carrier yielding a bracket (or None for the pool default).

    A bracket is itself a Nu term, so passing one directly would make it a
    *subtree* - compiled, validated and evaluated in the caller. It has to be
    carried as a value instead, exactly like ``Eval``'s carrier. Any other Nu
    is taken as the carrier as-is, so the bracket can come from a Ref.
    """
    from nu.core.spans.bracket import _LifecycleBracket as _Bracket

    if isinstance(init, _Bracket):
        return Literal(init)
    return init if isinstance(init, Nu) else Literal(init)


def _require_pool(value: object) -> WorkerPool:
    """Unwrap the pool slot's value, refusing sentinels with a usable message."""
    if value is EMPTY or value is INVALID or value is None:
        msg = "no WorkerPool is bound on the Context; wrap the tree in Provide(WorkerPool, ...)"
        raise RuntimeError(msg)
    if not isinstance(value, WorkerPool):
        msg = f"the pool slot yielded {type(value).__name__}, not a WorkerPool"
        raise TypeError(msg)
    return value


def _dispatch_body(body: object) -> Nu:
    """The ``Dispatch`` body: any Nu at all.

    Nothing here judges what the body yields. A dispatched body's value is
    dropped by design -- the parent never waits on it -- and whether that is
    what the caller wanted is the caller's business, not this constructor's.
    """
    if not isinstance(body, Nu):
        msg = f"Dispatch needs a Nu body, got {type(body).__name__}"
        raise TypeError(msg)
    return body


def _one_sync(value: object) -> Iterator:
    if value is not None:
        yield value


async def _one_async(value: object) -> AsyncIterator:
    if value is not None:
        yield value


# --- fleet membership -------------------------------------------------------


class Launch(ScalarAction):
    """Spawns one worker process in the pool and yields the id it got.

    The call returns once the child has finished building its Context and
    said READY, so the id it yields is immediately usable as a target.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        init: a lifecycle bracket this one worker comes up holding, overriding
            the pool's own. A bracket is carried as a value, so a Ref or any
            query yielding one works here too. None means "use the pool's".

    Notes:
        - Ids are monotonic and never reused, so an id kept past a ``Kill``
          reads as dead rather than pointing at some later worker.
        - This both mutates the pool and yields, which is why it is an action
          rather than a query: evaluating it twice launches two processes.
        - Under ``spawn`` (the default start method) the bracket is pickled
          into the child, so it has to be pickleable - top-level in a module,
          no closures.
        - A child that fails to build its Context is killed and reaped before
          the error propagates, so a failed launch leaves nothing behind.

    Yields:
        The new worker's id, an int.

    Example:
        Provide(WorkerPool, {"name": "nu"},
            SetCmd(AttrRef("w"), Launch()),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, init: _LifecycleBracket | Nu | None = None) -> None:
        super().__init__(_pool_node(pool), _init_node(init))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync launch thunk."""

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[0](rt))
            init = children[1](rt)
            return pool.launch(None if init is EMPTY or init is INVALID else init)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async launch thunk."""

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[0](rt))
            init = await children[1](rt)
            return await pool.alaunch(None if init is EMPTY or init is INVALID else init)

        return athunk


class Kill(Command):
    """Ends a worker now and reaps it.

    A real kill, not a cooperative stop: a worker busy running a resident body
    may never read its pipe again, so asking it nicely is asking to wait
    forever. The process gets SIGTERM, a short grace period, then SIGKILL, and
    is reaped either way.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id. Any Nu - a Literal, an
            ``AttrRef``, a query over a shape.

    Notes:
        - Idempotent. An id that was already killed, or was never launched at
          all, is a no-op rather than an error, so a retry or a double-kill in
          a race costs nothing.
        - It returns only once the process is reaped, so nothing is left in Z
          state behind it.
        - Anything still waiting on that worker - a ``Teleport`` in flight on
          another thread - fails with ``WorkerGone`` rather than hanging.

    Yields:
        Nothing.

    Example:
        Kill(worker=AttrRef("w"))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, worker: object = None) -> None:
        super().__init__(_pool_node(pool), worker)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync kill thunk."""

        def thunk(rt: Runtime) -> None:
            pool = _require_pool(children[0](rt))
            pool.kill(children[1](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async kill thunk."""

        async def athunk(rt: Runtime) -> None:
            pool = _require_pool(await children[0](rt))
            await pool.akill(await children[1](rt))

        return athunk


# --- running work -----------------------------------------------------------


class Dispatch(Command):
    """Ships the body to a worker and returns as soon as the child has it.

    The verb for resident work - a tree that subscribes, loops, serves, and is
    never expected to produce a value. The parent waits only for the child's
    acknowledgement of receipt, so a ``Dispatch`` sitting inside a
    ``ReactForever`` body never blocks that loop. Nothing ever awaits the
    dispatched body; the only things that end it are ``Kill`` and pool
    teardown.

    Use ``Teleport`` instead when the work finishes and the value is the
    point. Awaiting a reply from a resident body is the failure this split
    exists to design away.

    .. warning::

       **The body is payload, so it is not part of the tree.** Every pass Nu
       has - every walker, rewrite, analysis and the box-tree render -
       traverses ``_children``, and payload is opaque to all of them. A
       dispatched body is therefore invisible to whatever runs over the tree
       that contains the ``Dispatch``, and will be silently skipped rather
       than reported as unsupported.

       The caller owns that. Apply whatever passes the body needs *to the
       body*, before constructing the ``Dispatch``::

           Dispatch(body=some_pass(resident_tree), worker=AttrRef("w"))

       ``nu.kv.auto_flow_atomic`` is one such pass, and a good illustration of
       the cost: wrapping the enclosing tree leaves kv writes inside a
       dispatched body with no enclosing ``Transaction`` at run time, and
       nothing anywhere says so. It is an example, not the rule - the rule is
       that *no* pass reaches in here.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        body: the tree to run in the worker. Kept in ``_payload["body"]``,
            captured as a term, never evaluated in the caller.
        worker: the node yielding the worker id. Any Nu - the id is still a
            child, so it can be a ``Literal``, an ``AttrRef`` or a query.

    Notes:
        - It is a Command: it writes the pool through a Ref and yields
          nothing. That is also why the body cannot be a child - a Command's
          composition row holds value-yielding children only, and a resident
          body is usually a Flow.
        - Because the body is not a child, no law sees it either. A body whose
          root yields a value is refused in the constructor instead, since
          nothing would consume that value.
        - The body resolves its refs against the *worker's* Context, built in
          the child by the pool's (or the launch's) ``init`` bracket.
          Anything bound around the Dispatch in the caller's tree is not
          visible there.
        - ``carry=True`` copies the caller's ``ctx.attrs`` into a copy of the
          worker's Context for that one body, so loop variables bound by
          ``Map`` or ``Filter`` reach it.
        - Everything crossing the pipe is pickled, so the body term and what
          it captures must be pickleable.
        - Several bodies can be dispatched to one worker; they run as
          concurrent tasks in the child's loop. A body that blocks the loop
          rather than awaiting will starve its siblings, which is a property
          of the body, not of the pool.
        - An exception from a dispatched body is reported to the parent and
          dropped: there is no waiter to raise it in. ``Running`` going False
          is the only local signal that a body ended.

    Yields:
        Nothing.

    Example:
        Dispatch(body=resident_tree, worker=AttrRef("w"))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(
        self,
        pool: Nu | None = None,
        body: Nu | None = None,
        worker: object = None,
        *,
        carry: bool = False,
    ) -> None:
        super().__init__(_pool_node(pool), worker)
        # Payload is shared by every ``_with_children`` variant of this term.
        # That is safe here precisely because a Nu term is immutable: the body
        # cannot be mutated through one variant and seen from another. The
        # cost is the other half of the same fact - a rewrite that rebuilds
        # the children carries the *original* body across untouched.
        self._payload["body"] = _dispatch_body(body)
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync dispatch thunk."""
        body_term = self._payload["body"]
        carry = self._payload["carry"]

        def thunk(rt: Runtime) -> None:
            pool = _require_pool(children[0](rt))
            wid = children[1](rt)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            pool.dispatch(wid, body_term, attrs=attrs)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async dispatch thunk."""
        body_term = self._payload["body"]
        carry = self._payload["carry"]

        async def athunk(rt: Runtime) -> None:
            pool = _require_pool(await children[0](rt))
            wid = await children[1](rt)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            await pool.adispatch(wid, body_term, attrs=attrs)

        return athunk


class Teleport(Policy):
    """Runs the body in a pool worker and yields what it produced there.

    Request/reply, for work that finishes. A policy over where, not what: the
    body is captured as a term, never evaluated locally, and dropping the
    Teleport moves the work without changing it.

    The difference from ``Dispatch`` is the waiting. This one blocks until the
    child answers, which is correct for a computation and catastrophic for a
    resident tree.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        body: the Nu to run in the worker.
        worker: the node yielding the worker id. Any Nu, so the target can be
            computed - which is the whole point of this fabric's version.

    Notes:
        - The body is ``children[0]`` even though the constructor takes it
          second: a Span resolves its sort and cardinality from its first
          child, so anything else there would make the node present as a ref.
        - The body resolves its refs against the worker's Context.
          ``carry=True`` copies the caller's ``ctx.attrs`` across for that one
          execution.
        - Both runtimes work. The pipe read blocks either way; the sync path
          blocks the calling thread, the async path waits off-thread.
        - A stream-rooted body evaluates to an async generator, which cannot
          be pickled back. Reduce it inside the body with ``Collect`` or a
          fold before teleporting.
        - An exception raised in the child comes back and is re-raised here.
          One that cannot be pickled is replaced by a ``RuntimeError``
          carrying its type and message.
        - If the worker is killed while the call is in flight it raises
          ``WorkerGone`` rather than hanging.

    Yields:
        The value the body's root produced in the worker, None for an
        effect-only body. A stream-shaped consumer gets the collapsed remote
        value as a one-item stream.

    Example:
        Teleport(body=Collect(heavy_stream), worker=AttrRef("w"))
    """

    def __init__(
        self,
        pool: Nu | None = None,
        body: Nu | None = None,
        worker: object = None,
        *,
        carry: bool = False,
    ) -> None:
        super().__init__(body, _pool_node(pool), worker)
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync teleport thunk."""
        body_term = self._children[0]
        carry = self._payload["carry"]

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[1](rt))
            wid = children[2](rt)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = pool.teleport(wid, body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_sync(result)
            return result

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async teleport thunk."""
        body_term = self._children[0]
        carry = self._payload["carry"]

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[1](rt))
            wid = await children[2](rt)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = await pool.ateleport(wid, body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_async(result)
            return result

        return athunk


# --- reads ------------------------------------------------------------------


class Alive(ScalarQuery):
    """Whether the worker at this id is a process that is still up.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.

    Notes:
        - A pure parent-side read of the process state; the child is never
          contacted, so a worker wedged in a tight loop still reads alive.
        - An id that was killed, or never launched, reads False. Ids are never
          reused, so False is permanent for that id.

    Yields:
        True or False.

    Example:
        Alive(worker=AttrRef("w"))
    """

    def __init__(self, pool: Nu | None = None, worker: object = None) -> None:
        super().__init__(_pool_node(pool), worker)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync alive thunk."""

        def thunk(rt: Runtime) -> object:
            return _require_pool(children[0](rt)).alive(children[1](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async alive thunk."""

        async def athunk(rt: Runtime) -> object:
            return _require_pool(await children[0](rt)).alive(await children[1](rt))

        return athunk


class Running(ScalarQuery):
    """Whether a body dispatched to this worker is still executing.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.

    Notes:
        - Parent-side bookkeeping, not a ping: the answer is True from the
          child's acknowledgement of a ``Dispatch`` until it reports that body
          finished. So a worker that stops servicing its pipe does not turn
          this into a hang.
        - It counts dispatched bodies only. A ``Teleport`` in flight is the
          caller's own blocking call and is not reflected here.
        - A snapshot: the body can finish the instant after it is read.

    Yields:
        True or False.

    Example:
        Running(worker=AttrRef("w"))
    """

    def __init__(self, pool: Nu | None = None, worker: object = None) -> None:
        super().__init__(_pool_node(pool), worker)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync running thunk."""

        def thunk(rt: Runtime) -> object:
            return _require_pool(children[0](rt)).running(children[1](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async running thunk."""

        async def athunk(rt: Runtime) -> object:
            return _require_pool(await children[0](rt)).running(await children[1](rt))

        return athunk


class Workers(StreamQuery):
    """Every worker id the pool still tracks, in launch order.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.

    Notes:
        - Killed ids are gone from the stream; an id that is present may still
          be a dead process, which is what ``Alive`` is for.
        - The list is taken as a snapshot before the stream starts, so a
          concurrent launch or kill does not disturb the iteration.

    Yields:
        The worker ids, ints, ascending.

    Example:
        Collect(Workers())
    """

    def __init__(self, pool: Nu | None = None) -> None:
        super().__init__(_pool_node(pool))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync workers thunk."""

        def thunk(rt: Runtime) -> object:
            return iter(_require_pool(children[0](rt)).workers())

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async workers thunk."""

        async def athunk(rt: Runtime) -> object:
            ids = _require_pool(await children[0](rt)).workers()

            async def gen() -> AsyncIterator:
                for wid in ids:
                    yield wid

            return gen()

        return athunk
