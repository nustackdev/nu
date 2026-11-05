"""The interactions of the ``nustd.mp_pool`` fabric: the worker toolkit.

Ten atoms over one ``WorkerPool``, policy-free, each with a sync and an async
thunk that never blocks the event loop:

- create: ``Launch``, ``Workers``
- run work: ``Teleport``, ``Dispatch``, ``Cancel``
- stop work or the worker, by force: ``Interrupt`` (stop what runs, keep the
  worker), ``Stop`` (ask it to exit, escalate within grace), ``Kill`` (SIGKILL
  now). The pool's own close is the fourth level: ``Stop`` on every worker at
  once.
- inspect: ``Status``, ``Wait``

Because the fabric spans many processes, these are declarative statements
about its contents rather than imperative escapes - the same way
``ref.set()`` is a statement about a mem fabric.

**No caller value is payload.** Every worker id, job id, pool address, the
``init`` override, the stop ``grace`` and the wait ``timeout`` are children,
so any of them can come from a ``Ref``, a mem slot or any query.
``nustd.mp.Teleport`` keeps its target in ``self._payload``, which pins it at
construction time; that is the mistake this fabric exists not to repeat.

The one thing that *is* payload is ``Dispatch``'s body, and it is payload for
a structural reason, not a shortcut. See the warning on that class: a body in
payload is not part of the tree, so no walker reaches it.

Slot order, which is what the laws read:

==========  =========================  ============  ====================
atom        slots                      sort          mutates
==========  =========================  ============  ====================
Launch      (pool, init)               ScalarAction  {0}
Dispatch    (pool, worker)             ScalarAction  {0}
Teleport    (body, pool, worker)       Policy        -
Cancel      (pool, worker, job)        Command       {0}
Interrupt   (pool, worker)             Command       {0}
Stop        (pool, worker, grace)      ScalarAction  {0}
Kill        (pool, worker)             Command       {0}
Status      (pool, worker)             ScalarQuery   -
Wait        (pool, worker, timeout)    ScalarQuery   -
Workers     (pool,)                    StreamQuery   -
==========  =========================  ============  ====================

``Dispatch`` carries its body in ``_payload["body"]``; ``Teleport`` carries
its body as ``children[0]``. The asymmetry is intended:

- ``Cancel``, ``Interrupt`` and ``Kill`` are VOID mutators, so ``ref_slots``
  requires the mutation slot to hold a Ref. The pool ref is slot 0 in all of
  them, and in every other mutator too.
- A resident body is typically a Flow (``ForeverDo``, ``ReactEvery``), and a
  Flow in an Interaction's composition row does not compose, so
  ``Dispatch``'s body cannot be a child - hence the payload.
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
from nu.lang.null import is_null

from .refs import PoolRef
from .resources import WorkerPool


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang.runtime import Runtime


__all__ = [
    "Cancel",
    "Dispatch",
    "Interrupt",
    "Kill",
    "Launch",
    "Status",
    "Stop",
    "Teleport",
    "Wait",
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
    """Unwrap the pool slot's value, refusing NULL with a usable message."""
    if is_null(value) or value is None:
        msg = "no WorkerPool is bound on the Context; wrap the tree in Provide(WorkerPool, ...)"
        raise RuntimeError(msg)
    if not isinstance(value, WorkerPool):
        msg = f"the pool slot yielded {type(value).__name__}, not a WorkerPool"
        raise TypeError(msg)
    return value


def _optional(value: object) -> object:
    """A child that may be left out: NULL reads as None."""
    return None if is_null(value) else value


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


# --- create -----------------------------------------------------------------


class Launch(ScalarAction):
    """Hands out one worker process from the pool and yields its id.

    A warm spare when the pool keeps some (``spares=``) and this launch uses
    the pool's own ``init``; otherwise a fresh spawn. Either way the call
    returns once the child has built its Context and said ``ready``, so the
    id it yields is immediately usable as a target.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        init: a lifecycle bracket this one worker comes up holding, overriding
            the pool's own. A bracket is carried as a value, so a Ref or any
            query yielding one works here too. None means "use the pool's".

    Notes:
        - Ids are monotonic and never reused, so an id kept past a ``Kill``
          reads as gone rather than pointing at some later worker.
        - This both mutates the pool and yields, which is why it is an action
          rather than a query: evaluating it twice hands out two workers.
        - A worker with its own ``init`` is always spawned cold: the spares
          hold the pool's.
        - The bracket goes into the child through cloudpickle, so it may hold
          closures and locally defined classes.
        - A child that fails to build its Context is ended before the error
          propagates, so a failed launch leaves nothing behind. Cancelled
          midway, the launch still finishes on its thread and the worker is
          killed.

    Yields:
        The worker's id, an int.

    Example:
        nu.let(Launch(), lambda w: Stop(worker=w))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, init: _LifecycleBracket | Nu | None = None) -> None:
        super().__init__(_pool_node(pool), _init_node(init))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync launch thunk."""

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[0](rt))
            return pool.launch(_optional(children[1](rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async launch thunk."""

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[0](rt))
            return await pool.alaunch(_optional(await children[1](rt)))  # type: ignore[arg-type]

        return athunk


class Workers(StreamQuery):
    """Every live worker the pool has handed out, in launch order.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.

    Notes:
        - Live only. A worker that exited, on its own or by a ``Stop`` or a
          ``Kill``, drops out by itself; ``Status`` still reads it.
        - Spares waiting on the shelf are not listed until a ``Launch`` takes
          one.
        - The list is taken as a snapshot before the stream starts, so a
          concurrent launch or exit does not disturb the iteration.

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


# --- run work ---------------------------------------------------------------


class Teleport(Policy):
    """Runs the body in a pool worker and yields what it produced there.

    Request/reply, for work that finishes. A policy over where, not what: the
    body is captured as a term, never evaluated locally, and dropping the
    Teleport moves the work without changing it.

    The difference from ``Dispatch`` is the waiting. This one blocks until the
    child answers, which is correct for a computation and wrong for a
    resident tree nobody means to wait on.

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
        - The sync path blocks the calling thread for the reply; the async
          path holds no thread, the pool's reader wakes it.
        - A stream-rooted body evaluates to an async generator, which cannot
          be pickled back. Reduce it inside the body with ``Collect`` or a
          fold before teleporting.
        - An exception raised in the child comes back and is re-raised here.
          One that cannot be pickled is replaced by a ``RuntimeError``
          carrying its type and message.
        - A body ended by ``Interrupt`` raises ``Interrupted``; the worker is
          still there. A worker that is gone, or goes while this waits,
          raises ``WorkerGone`` with its cause and exit code.
        - Cancelled while it waits (a losing ``Race`` branch, a cancelled
          task), the body is cancelled in the worker too and unwinds through
          its own cleanup there. The cancel is sent, not awaited.

    Yields:
        The value the body's root produced in the worker, None for an
        effect-only body. A stream-shaped consumer gets the collapsed remote
        value as a one-item stream.

    Example:
        Teleport(body=Collect(heavy_stream), worker=Local.worker)
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
            attrs = dict(rt.ctx.attrs.items()) if carry else None
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
            attrs = dict(rt.ctx.attrs.items()) if carry else None
            result = await pool.ateleport(wid, body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_async(result)
            return result

        return athunk


class Dispatch(ScalarAction):
    """Ships the body to a worker, returns as soon as the child has it, and yields its job id.

    The verb for resident work - a tree that subscribes, loops, serves, and is
    never expected to produce a value. The parent waits only for the child's
    acknowledgement of receipt, so a ``Dispatch`` sitting inside a
    ``ReactEvery`` body never blocks that loop. Nothing ever awaits the
    dispatched body; it ends by itself, by ``Cancel`` with the job id this
    yields, by ``Interrupt``, or with the worker.

    Use ``Teleport`` instead when the work finishes and the value is the
    point.

    .. warning::

       **The body is payload, so it is not part of the tree.** Every pass Nu
       has - every walker, rewrite, analysis and the box-tree render -
       traverses ``_children``, and payload is opaque to all of them. A
       dispatched body is therefore invisible to whatever runs over the tree
       that contains the ``Dispatch``, and will be silently skipped rather
       than reported as unsupported.

       The caller owns that. Apply whatever passes the body needs *to the
       body*, before constructing the ``Dispatch``::

           Dispatch(body=some_pass(resident_tree), worker=Local.worker)

       ``nustd.kv.auto_flow_atomic`` is one such pass, and a good illustration of
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
            child, so it can be a ``Literal``, a mem slot or a query.

    Notes:
        - An action: it mutates the pool and yields the job id, the handle
          ``Cancel`` takes. A caller that never gets the id (cancelled before
          the ack, or the ack did not come within the pool's
          ``ack_timeout``) could never cancel the body, so it is cancelled
          for them.
        - The body is not a child because a resident body is usually a Flow,
          which does not compose in an Interaction's slots.
        - The body resolves its refs against the *worker's* Context, built in
          the child by the pool's (or the launch's) ``init`` bracket.
          Anything bound around the Dispatch in the caller's tree is not
          visible there. ``carry=True`` binds the caller's ``ctx.attrs`` on a
          branch of the worker's Context for that one body, so loop
          variables bound by ``Map`` or ``Filter`` reach it.
        - Everything crossing the pipe goes through cloudpickle, so the body
          term may hold closures and locally defined classes.
        - Several bodies can be dispatched to one worker; they run as
          concurrent tasks in the child's loop. A body that blocks the loop
          rather than awaiting will starve its siblings, which is a property
          of the body, not of the pool.
        - An exception from a dispatched body has nobody to raise at: it is
          logged (``logging``, logger ``nustd.mp_pool``) and kept on the
          worker's ``Status`` as ``errors``. The job id leaves the status's
          ``jobs`` when the body ends, however it ends.

    Yields:
        The job id, an int.

    Example:
        nu.let(Dispatch(body=resident_tree, worker=w), lambda job: Cancel(worker=w, job=job))
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

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[0](rt))
            wid = children[1](rt)
            attrs = dict(rt.ctx.attrs.items()) if carry else None
            return pool.dispatch(wid, body_term, attrs=attrs)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async dispatch thunk."""
        body_term = self._payload["body"]
        carry = self._payload["carry"]

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[0](rt))
            wid = await children[1](rt)
            attrs = dict(rt.ctx.attrs.items()) if carry else None
            return await pool.adispatch(wid, body_term, attrs=attrs)

        return athunk


class Cancel(Command):
    """Cancels one dispatched body on a worker, cooperatively.

    The task running it in the child is cancelled (an asyncio cancel), so the
    body unwinds through its own ``finally`` blocks there. The worker and its
    other jobs carry on.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.
        job: the node yielding the job id ``Dispatch`` yielded.

    Notes:
        - Fire and forget: the cancel is sent, nothing waits for the body to
          finish unwinding. ``Status``'s ``jobs`` drops the id once it has.
        - A no-op for a job that already ended, an unknown job id, and a
          worker that is gone or was never launched.
        - Cooperative only: a body stuck in sync code never sees it. That is
          what ``Interrupt`` is for.

    Yields:
        Nothing.

    Example:
        nu.let(Dispatch(body=resident, worker=w), lambda job: Cancel(worker=w, job=job))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, worker: object = None, job: object = None) -> None:
        super().__init__(_pool_node(pool), worker, job)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync cancel thunk."""

        def thunk(rt: Runtime) -> None:
            pool = _require_pool(children[0](rt))
            pool.cancel(children[1](rt), children[2](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async cancel thunk."""

        async def athunk(rt: Runtime) -> None:
            pool = _require_pool(await children[0](rt))
            await pool.acancel(await children[1](rt), await children[2](rt))

        return athunk


# --- stop work or the worker ------------------------------------------------


class Interrupt(Command):
    """Stops what a worker is running and keeps the worker.

    SIGINT to the worker's process group. A body blocked in sync code gets
    ``KeyboardInterrupt`` where it stands, the other jobs are cancelled, and
    the worker goes on to take the next request. Subprocesses a body started
    get the SIGINT too, the way a terminal's Ctrl+C reaches them.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.

    Notes:
        - Every job on the worker ends: a ``Teleport`` waiting on one raises
          ``Interrupted``, a dispatched one just ends.
        - Never blocks: the signal is sent and that is all. It is a point in
          time: a request still in the pipe, not yet received by the
          worker, is not running and is not ended.
        - A body running part of itself in tasks of its own (``Parallel``
          with async placement) is reached in whichever task holds the loop.
        - A no-op on a worker that is gone or was never launched.
        - A body that catches ``KeyboardInterrupt`` and carries on is the
          body's choice; ``Stop`` and ``Kill`` are the stronger rungs.

    Yields:
        Nothing.

    Example:
        Interrupt(worker=Local.worker)
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, worker: object = None) -> None:
        super().__init__(_pool_node(pool), worker)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync interrupt thunk."""

        def thunk(rt: Runtime) -> None:
            _require_pool(children[0](rt)).interrupt(children[1](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async interrupt thunk."""

        async def athunk(rt: Runtime) -> None:
            _require_pool(await children[0](rt)).interrupt(await children[1](rt))

        return athunk


class Stop(ScalarAction):
    """Asks a worker to exit cleanly, escalates if it does not, and yields its status after.

    The ladder, under one budget ``grace``: the ``stop`` frame first, so its
    jobs are cancelled, their ``finally`` blocks and the init teardown run and
    the process exits 0; SIGINT to its group at 60% of ``grace``, SIGTERM at
    80%, SIGKILL at 95%. Returns once the worker is gone, and by ``grace``
    whatever happened.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.
        grace: the node yielding the budget in seconds. None (the default)
            means the pool's ``grace``.

    Notes:
        - The status says how it went: ``cause`` is ``"stopped"`` for an end
          before the SIGTERM rung, ``"killed"`` for one that needed SIGTERM
          or SIGKILL, and ``exitcode`` is 0 for a clean stop, 143 for one the
          SIGTERM rung ended.
        - A worker already gone yields its record at once; an id never
          launched raises ``UnknownWorker``.
        - On the async path nothing blocks the loop. Cancelled midway, the
          worker gets SIGKILL before the cancellation goes on up.
        - Anything waiting on the worker (a ``Teleport``) fails with
          ``WorkerGone`` once it is gone.

    Yields:
        The worker's ``WorkerStatus``, ``state == "exited"`` unless the
        process outlived even the SIGKILL (a process stuck in the kernel).

    Example:
        Stop(worker=Local.worker, grace=2.0)
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, worker: object = None, grace: object = None) -> None:
        super().__init__(_pool_node(pool), worker, grace)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync stop thunk."""

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[0](rt))
            return pool.stop(children[1](rt), _optional(children[2](rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async stop thunk."""

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[0](rt))
            grace = _optional(await children[2](rt))
            return await pool.astop(await children[1](rt), grace)  # type: ignore[arg-type]

        return athunk


class Kill(Command):
    """Ends a worker now: SIGKILL to its whole process group.

    The rung for a worker that will not stop. No teardown runs in it, and
    every subprocess its bodies started goes with it. Returns once the
    process is reaped, which takes milliseconds, and never longer than the
    pool's ``grace``.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id. Any Nu - a Literal, a
            mem slot, a query over a shape.

    Notes:
        - Idempotent. An id that is already gone, or was never launched at
          all, is a no-op rather than an error, so a retry or a double kill
          in a race costs nothing.
        - Anything still waiting on that worker - a ``Teleport`` in flight on
          another branch - fails with ``WorkerGone`` (cause ``"killed"``,
          exit code -9) rather than hanging.
        - On the async path the signal is out before the first await, so a
          cancelled Kill has still killed the worker.
        - Use ``Stop`` for an end that lets the worker clean up.

    Yields:
        Nothing.

    Example:
        Kill(worker=Local.worker)
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


# --- inspect ----------------------------------------------------------------


class Status(ScalarQuery):
    """Everything the pool knows about one worker, as one record, alive or gone.

    A read of the parent's books: the child is never contacted, so a worker
    wedged in a tight loop still answers, and the read never blocks.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.

    Notes:
        - ``state`` is one of ``"starting"``, ``"idle"``, ``"busy"``,
          ``"stopping"``, ``"exited"``. Whether a worker is alive is
          ``state != "exited"``; whether it runs anything is ``jobs``.
        - ``pid``, ``pgid``, ``name`` and ``started_at`` identify the
          process; ``name`` is what ``ps`` shows, ``nu:{pool name}-{id}``.
        - Once exited, ``exitcode`` and ``cause`` say how: ``"stopped"``,
          ``"killed"``, ``"crashed"``, ``"init_failed"`` or ``"parent_died"``.
        - ``errors`` keeps the last errors the worker's dispatched bodies
          raised, as ``(job, exception)`` pairs.
        - Readable after the worker is gone, for the last thousand or so
          exits. An id never launched raises ``UnknownWorker``.
        - A snapshot: the worker can change the instant after it is read.

    Yields:
        A ``WorkerStatus``.

    Example:
        Status(worker=Local.worker)
    """

    def __init__(self, pool: Nu | None = None, worker: object = None) -> None:
        super().__init__(_pool_node(pool), worker)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync status thunk."""

        def thunk(rt: Runtime) -> object:
            return _require_pool(children[0](rt)).status(children[1](rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async status thunk."""

        async def athunk(rt: Runtime) -> object:
            return _require_pool(await children[0](rt)).status(await children[1](rt))

        return athunk


class Wait(ScalarQuery):
    """Waits until a worker has exited, at most ``timeout``, and yields its status.

    The one read here that takes time: it completes when the process is gone,
    whether it ended on its own, crashed, or was stopped or killed from
    another branch. It observes the exit and causes nothing, so it stays a
    query.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        worker: the node yielding the worker id.
        timeout: the node yielding the longest wait in seconds. None (the
            default) waits as long as it takes.

    Notes:
        - The exit is seen through the process itself (a pidfd on Linux, a
          kqueue on mac), so a pipe a grandchild still holds open does not
          keep it waiting.
        - On a timeout it yields the status as it stands, ``state`` not
          ``"exited"``, rather than raising.
        - A worker already gone yields its record at once; an id never
          launched raises ``UnknownWorker``.
        - On the async path nothing polls and no thread is held: the pool's
          reader thread wakes it on its own loop. Cancelling the Wait just
          drops the waiter. The sync path blocks the calling thread.

    Yields:
        A ``WorkerStatus``.

    Example:
        Race(Wait(worker=Local.worker), stop_signal)
    """

    def __init__(
        self, pool: Nu | None = None, worker: object = None, timeout: object = None
    ) -> None:
        super().__init__(_pool_node(pool), worker, timeout)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync wait thunk."""

        def thunk(rt: Runtime) -> object:
            pool = _require_pool(children[0](rt))
            return pool.wait(children[1](rt), _optional(children[2](rt)))  # type: ignore[arg-type]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async wait thunk."""

        async def athunk(rt: Runtime) -> object:
            pool = _require_pool(await children[0](rt))
            timeout = _optional(await children[2](rt))
            return await pool.await_exit(await children[1](rt), timeout)  # type: ignore[arg-type]

        return athunk
