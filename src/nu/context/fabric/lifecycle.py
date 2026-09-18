"""``Provide`` brackets: construct + bind fabrics for the body's duration.

The tree carries a *class* plus a *spec* (kwargs, list of kwargs, or dict of
kwargs). On entry each bracket constructs its fabric(s), runs setup, binds on
ctx. On exit teardown fires in reverse (LIFO), so an outer fabric is still
live while inner ones tear down.

Three primitives, one per attach shape:

    Provide(cls, kwargs, body, *, tag=None, tags=(), predicate=None)
        # bind ONE instance keyed by (cls, *tags)

    ProvideList(cls, [kwargs_a, kwargs_b, ...], body,
                *, base_tag=0, extra_tags=(), predicate=None)
        # bind N instances at (cls, base_tag+0, *extra_tags), ...

    ProvideDict(cls, {"k1": kwargs_a, ...}, body,
                *, extra_tags=(), predicate=None)
        # bind N instances at (cls, "k1", *extra_tags), ...

Tag knobs (all optional, they compose):

- ``tag=`` on ``Provide`` is sugar for a single-tag ``tags=(tag,)``.
- ``tags=`` binds under an unordered set of tags; ``ctx.get(cls, t)`` matches
  when ``t`` is a subset of the bound set (specificity fallback).
- ``predicate=`` is a single guard callable forwarded into Context's guarded
  registry: ``ctx.get(cls, *tags, **data)`` resolves this binding only when
  ``predicate(**data)`` returns True. Useful for "bind a Navigator whose
  shard covers this address" without pre-computing all shard tags.

The ecosystem is open: ``ProvideSharded``, ``ProvideRoundRobin``,
``ProvideReplicated``, ``ProvideLazy``, etc. all follow the same shape - each
is a Bracket subclass; the engine sees them as regular lifecycle spans.

Both sync and async runs are supported natively via the two open methods
(``_open`` and ``_aopen``). Under the async runtime the bracket prefers
``asetup`` / ``acleanup`` if the fabric defines them, and falls back to
``setup`` / ``cleanup`` otherwise. Under the sync runtime, only sync methods
run - an async-only fabric fails at setup with a clear error.

``FabricLifecycle`` protocol (all methods optional, checked with ``hasattr``):

    def setup(self, ctx): ...        # sync run, or async fallback
    def cleanup(self): ...
    async def asetup(self, ctx): ... # async run (preferred)
    async def acleanup(self): ...
"""

from __future__ import annotations

from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.core.spans.bracket import _LifecycleBracket


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator, Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["Provide", "ProvideDict", "ProvideList", "With"]


# =========================================================================
# construction / lifecycle helpers
# =========================================================================


def _construct(cls: type, kwargs: Mapping[str, object]) -> object:
    """Build one resource from ``cls(**kwargs)``."""
    return cls(**kwargs)


def _refuse_async_only(cls: type) -> None:
    """Sync path guard: refuse classes marked ``_nu_async_only``.

    Called before instance construction so a mis-provisioned tree fails at
    the leaf ``Provide`` with a clear message, instead of half-building an
    instance whose ``asetup`` we can't drive.
    """
    if getattr(cls, "_nu_async_only", False):
        msg = f"{cls.__name__} requires the async runner (nu.arun); marked _nu_async_only"
        raise RuntimeError(msg)


def _setup(instance: object, ctx: Context) -> None:
    """Call sync ``setup(ctx)``; raise if the fabric only defines ``asetup``.

    Fabrics with neither ``setup`` nor ``asetup`` are lifecycle-free (e.g.
    ``Codec``) and pass through. Fabrics with only ``asetup`` are async-only
    in shape and raise here so misuse doesn't corrupt the ctx binding.
    """
    if hasattr(instance, "setup"):
        instance.setup(ctx)
        return
    if hasattr(instance, "asetup"):
        msg = f"{type(instance).__name__} has no sync setup; use nu.arun or add setup()"
        raise RuntimeError(msg)


async def _asetup(instance: object, ctx: Context) -> None:
    """Prefer async ``asetup(ctx)``, fall back to sync ``setup(ctx)`` if defined."""
    if hasattr(instance, "asetup"):
        await instance.asetup(ctx)
    elif hasattr(instance, "setup"):
        instance.setup(ctx)


def _teardown(instances: Sequence[object]) -> None:
    """Sync teardown, LIFO."""
    for inst in reversed(instances):
        if hasattr(inst, "cleanup"):
            inst.cleanup()


async def _ateardown(instances: Sequence[object]) -> None:
    """Async teardown, LIFO. Prefers ``acleanup``, falls back to ``cleanup``."""
    for inst in reversed(instances):
        if hasattr(inst, "acleanup"):
            await inst.acleanup()
        elif hasattr(inst, "cleanup"):
            inst.cleanup()


def _merge_tags(tag: object, tags: Sequence[object]) -> tuple[object, ...]:
    """Fold ``tag=`` sugar + ``tags=`` seq into one positional tuple."""
    seq = tuple(tags)
    return seq if tag is None else (tag, *seq)


def _bind(
    ctx: Context,
    cls: type,
    inst: object,
    tags: Sequence[object],
    predicate: Callable | None,
) -> Context:
    """Bind ``inst`` on ``ctx`` under ``cls`` + tags, optionally guarded."""
    if predicate is None:
        return ctx.bind(cls, inst, *tags)
    return ctx.bind(cls, inst, *tags, predicate=predicate)


# =========================================================================
# Provide - one instance
# =========================================================================


class Provide(_LifecycleBracket):
    """Constructs one fabric and binds it on the Context for the body's duration.

    This is how a stateful Nu program gets its state: nothing in the tree
    reaches a fabric that was not provided around it. On entry the bracket
    builds ``cls(**kwargs)``, runs its setup if it has one, and binds the
    instance on the Context under the class plus any tags. The body runs
    against that Context. On exit teardown fires, and it fires in reverse
    order across nested brackets, so an outer fabric is still live while the
    ones inside it are tearing down.

    Args:
        cls: the fabric class to construct. Also the key it binds under,
            unless ``bind_as`` or the class's own ``_nu_bind_as`` overrides
            that.
        kwargs: passed straight to the constructor. Plain Python values, not
            Nu terms; this is a payload, not a child.
        body: the tree that runs with the fabric bound.

    Notes:
        - ``tag=`` is sugar for a one-element ``tags=``; both fold into the
          same tuple, and a tagged binding is read back by a Ref that carries
          the same tag. Resolution falls back from more tags to fewer, so a
          tagless read never reaches a tagged binding.
        - ``predicate=`` is one guard callable handed to the Context's
          guarded registry: the binding resolves only when
          ``predicate(**data)`` returns True for the data passed to
          ``ctx.get``. Useful for "the shard that covers this address"
          without enumerating shard tags up front.
        - ``bind_as=`` binds the instance under a different type than it was
          constructed from, so an implementation can be provided where a
          protocol or base class is what the tree asks for.
        - Setup is optional. A class with neither ``setup`` nor ``asetup``
          passes through untouched; one with only ``asetup`` raises under the
          sync runner rather than binding half-built, and a class marked
          ``_nu_async_only`` is refused before it is even constructed.
        - Under ``nu.arun`` the bracket prefers ``asetup`` / ``acleanup`` and
          falls back to the sync pair; under ``nu.run`` only the sync pair
          runs.
        - Teardown only reaches instances whose setup completed, so a setup
          that raises does not leave a half-open fabric to be cleaned up.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket. For a stream body the fabric stays bound for the
        whole drain and tears down when the stream is exhausted.

    Example:
        >>> class Counter:
        ...     def __init__(self, start=0):
        ...         self.n = start
        >>> nu.run(nu.Provide(Counter, {"start": 5}, nu.FabricRef(Counter).exists()))[0]
        True
    """

    def __init__(
        self,
        cls: type,
        kwargs: Mapping[str, object] | None = None,
        body: Nu | None = None,
        *,
        tag: object = None,
        tags: Sequence[object] = (),
        predicate: Callable | None = None,
        bind_as: type | None = None,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["kwargs"] = dict(kwargs or {})
        self._payload["tags"] = _merge_tags(tag, tags)
        self._payload["predicate"] = predicate
        self._payload["bind_as"] = bind_as

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        _refuse_async_only(cls)
        kwargs = self._payload["kwargs"]
        tags = self._payload["tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls

        instance = _construct(cls, kwargs)
        setup_done: list[object] = []
        try:
            _setup(instance, ctx)
            setup_done.append(instance)
            yield _bind(ctx, bind_as, instance, tags, predicate)
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        cls = self._payload["cls"]
        kwargs = self._payload["kwargs"]
        tags = self._payload["tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls

        instance = _construct(cls, kwargs)
        setup_done: list[object] = []
        try:
            await _asetup(instance, ctx)
            setup_done.append(instance)
            yield _bind(ctx, bind_as, instance, tags, predicate)
        finally:
            await _ateardown(setup_done)


# =========================================================================
# ProvideList - N instances by index
# =========================================================================


class ProvideList(_LifecycleBracket):
    """Constructs a fleet of one class and binds each member under its index.

    The list shape of :class:`Provide`: one instance per spec, bound at
    ``base_tag + i`` so the fleet is addressed by position. Each instance is
    constructed, set up and bound before the next one is built, so a later
    member's setup sees the earlier ones already on the Context.

    Args:
        cls: the fabric class every member is constructed from.
        specs: one kwargs mapping per instance, in the order they are built.
        body: the tree that runs with the whole fleet bound.

    Notes:
        - Index tags count from ``base_tag=``, which lets two fleets of the
          same class share one index space without colliding.
        - ``extra_tags=`` fold onto every member after its index tag, so the
          fleet can carry a shared label as well as a position.
        - ``predicate=`` is one guard callable shared by every member.
        - Teardown is reverse of setup and only reaches members whose setup
          completed, so a spec that fails mid-fleet unwinds the ones already
          built before the error propagates.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket.

    Example:
        nu.ProvideList(
            RayService,
            [{"port": 8000}, {"port": 8001}],
            body=feed,
            extra_tags=("ledger",),
        )
    """

    def __init__(
        self,
        cls: type,
        specs: Sequence[Mapping[str, object]],
        body: Nu | None = None,
        *,
        base_tag: int = 0,
        extra_tags: Sequence[object] = (),
        predicate: Callable | None = None,
        bind_as: type | None = None,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["specs"] = [dict(s) for s in specs]
        self._payload["base_tag"] = base_tag
        self._payload["extra_tags"] = tuple(extra_tags)
        self._payload["predicate"] = predicate
        self._payload["bind_as"] = bind_as

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        _refuse_async_only(cls)
        specs = self._payload["specs"]
        base = self._payload["base_tag"]
        extra = self._payload["extra_tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls

        setup_done: list[object] = []
        try:
            for i, kwargs in enumerate(specs):
                inst = _construct(cls, kwargs)
                _setup(inst, ctx)
                setup_done.append(inst)
                ctx = _bind(ctx, bind_as, inst, (base + i, *extra), predicate)
            yield ctx
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        cls = self._payload["cls"]
        specs = self._payload["specs"]
        base = self._payload["base_tag"]
        extra = self._payload["extra_tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls

        setup_done: list[object] = []
        try:
            for i, kwargs in enumerate(specs):
                inst = _construct(cls, kwargs)
                await _asetup(inst, ctx)
                setup_done.append(inst)
                ctx = _bind(ctx, bind_as, inst, (base + i, *extra), predicate)
            yield ctx
        finally:
            await _ateardown(setup_done)


# =========================================================================
# ProvideDict - N instances by key
# =========================================================================


class ProvideDict(_LifecycleBracket):
    """Constructs a fleet of one class and binds each member under its own key.

    The mapping shape of :class:`Provide`: same as :class:`ProvideList` but
    addressed by the caller's key rather than by position, which is what you
    want when the members are named rather than numbered.

    Args:
        cls: the fabric class every member is constructed from.
        specs: a mapping of key to kwargs. Each key becomes the tag its
            instance binds under.
        body: the tree that runs with the whole fleet bound.

    Notes:
        - Members are built in the mapping's insertion order, and teardown is
          the reverse of that.
        - ``extra_tags=`` fold onto every member after its key tag;
          ``predicate=`` is one guard callable shared by every member.
        - ``parallel=True`` fires every ``asetup`` concurrently instead of in
          sequence. Each one then sees the Context as it was on entry rather
          than one carrying the earlier members, so it is only safe when the
          fleet does not cross-depend. It is an async-only knob; the sync
          path ignores it. Teardown stays sequential and reversed either way.
        - A spec that fails unwinds the members already set up before the
          error propagates.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket.

    Example:
        nu.ProvideDict(
            RayService,
            {"ledger": {"port": 8000}, "index": {"port": 8001}},
            body=feed,
        )
    """

    def __init__(
        self,
        cls: type,
        specs: Mapping[object, Mapping[str, object]],
        body: Nu | None = None,
        *,
        extra_tags: Sequence[object] = (),
        predicate: Callable | None = None,
        bind_as: type | None = None,
        parallel: bool = False,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["specs"] = {k: dict(v) for k, v in specs.items()}
        self._payload["extra_tags"] = tuple(extra_tags)
        self._payload["predicate"] = predicate
        self._payload["bind_as"] = bind_as
        self._payload["parallel"] = parallel

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        _refuse_async_only(cls)
        specs = self._payload["specs"]
        extra = self._payload["extra_tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls

        setup_done: list[object] = []
        try:
            for key, kwargs in specs.items():
                inst = _construct(cls, kwargs)
                _setup(inst, ctx)
                setup_done.append(inst)
                ctx = _bind(ctx, bind_as, inst, (key, *extra), predicate)
            yield ctx
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        import asyncio

        cls = self._payload["cls"]
        specs = self._payload["specs"]
        extra = self._payload["extra_tags"]
        predicate = self._payload["predicate"]
        bind_as = self._payload.get("bind_as") or getattr(cls, "_nu_bind_as", None) or cls
        parallel = self._payload.get("parallel", False)

        setup_done: list[object] = []
        try:
            if parallel:
                keyed = [(key, _construct(cls, kw)) for key, kw in specs.items()]
                await asyncio.gather(*(_asetup(inst, ctx) for _, inst in keyed))
                setup_done.extend(inst for _, inst in keyed)
                for key, inst in keyed:
                    ctx = _bind(ctx, bind_as, inst, (key, *extra), predicate)
            else:
                for key, kwargs in specs.items():
                    inst = _construct(cls, kwargs)
                    await _asetup(inst, ctx)
                    setup_done.append(inst)
                    ctx = _bind(ctx, bind_as, inst, (key, *extra), predicate)
            yield ctx
        finally:
            await _ateardown(setup_done)


# =========================================================================
# With - N-ary bracket sequencer
# =========================================================================


class With(_LifecycleBracket):
    """Enters several lifecycle brackets around one body, tearing down in reverse.

    Python's ``with A, B, C: body``, in the tree. Each bracket is opened in
    order and the Context accumulates across them, so a later bracket's setup
    sees everything the earlier ones bound. The body runs against the final
    Context, and on exit teardown fires in reverse. What it buys is flatness:
    stacking peers at one level instead of the
    ``Provide(a, kw, Provide(b, kw, Provide(c, kw, body)))`` cascade.

    Args:
        *brackets: the lifecycle brackets to enter, in order.
        body: the tree that runs with all of them open.

    Notes:
        - Each bracket is used as a spec, not as a subtree: ``With`` re-enters
          its open/close and ignores whatever sits in that bracket's own body
          slot, so passing a body to a nested bracket has no effect.
        - Composes anything with the lifecycle shape - ``Provide``,
          ``ProvideList``, ``ProvideDict``, ``InvisiblesProxy`` and the rest.
        - A bracket whose setup raises unwinds the ones already entered
          before the error propagates.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket.

    Example:
        nu.With(
            nu.Provide(RayCluster, {...}),
            nu.Provide(RayService, {...}, tag="A"),
            nu.Provide(RayService, {...}, tag="B"),
            nu.ProvideDict(RayService, {...}),
            body=feed,
        )
    """

    def __init__(
        self,
        *brackets: _LifecycleBracket,
        body: Nu | None = None,
    ) -> None:
        super().__init__(body)
        self._payload["brackets"] = tuple(brackets)

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        brackets = self._payload["brackets"]
        with ExitStack() as stack:
            for b in brackets:
                ctx = stack.enter_context(b._open(ctx))
            yield ctx

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        brackets = self._payload["brackets"]
        async with AsyncExitStack() as stack:
            for b in brackets:
                ctx = await stack.enter_async_context(b._aopen(ctx))
            yield ctx
