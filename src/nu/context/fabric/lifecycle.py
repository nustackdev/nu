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

from nu.spans.bracket import _LifecycleBracket


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


def _setup(instance: object, ctx: Context) -> None:
    """Call sync ``setup(ctx)`` if defined."""
    if hasattr(instance, "setup"):
        instance.setup(ctx)


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
    """Construct ONE resource of ``cls(**kwargs)``, bind on ctx.

    On entry:
        - instance = cls(**kwargs)
        - if instance has setup / asetup, call it (async run prefers asetup)
        - ctx.bind(cls, instance, *tags [, predicate=predicate])
    On exit:
        - cleanup / acleanup (if defined)

    ``tag=`` is single-tag sugar; ``tags=`` is a multi-tag sequence; both fold
    into the same tag tuple. ``predicate=`` is one guard callable forwarded
    into Context's guarded registry.
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

    def __repr__(self) -> str:
        cls = self._payload["cls"]
        tags = self._payload["tags"]
        pred = self._payload["predicate"]
        parts = [cls.__name__]
        if tags:
            parts.append(f"tags={tags!r}")
        if pred is not None:
            parts.append(f"predicate={getattr(pred, '__name__', repr(pred))}")
        return f"Provide({', '.join(parts)})"


# =========================================================================
# ProvideList - N instances by index
# =========================================================================


class ProvideList(_LifecycleBracket):
    """Construct N resources of ``cls``, bind each on ctx at ``base_tag + i``.

    ``specs`` is a list of kwargs dicts, one per instance. Setup runs in
    order; teardown in reverse. If any setup raises, already-setup instances
    are torn down in reverse before propagating.

    ``extra_tags=`` fold onto every element after its index tag (shared
    across the fleet); ``predicate=`` fold onto every element as a shared
    guard.
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

    def __repr__(self) -> str:
        cls = self._payload["cls"]
        n = len(self._payload["specs"])
        return f"ProvideList({cls.__name__}, n={n})"


# =========================================================================
# ProvideDict - N instances by key
# =========================================================================


class ProvideDict(_LifecycleBracket):
    """Construct resources of ``cls`` keyed by a mapping, bind each by key.

    ``specs`` is a dict ``{key: kwargs}``. Setup runs in insertion order;
    teardown in reverse. Same failure semantics as :class:`ProvideList`.

    ``extra_tags=`` fold onto every element after its key tag; ``predicate=``
    fold onto every element as a shared guard.

    ``parallel=True`` fires all ``asetup`` calls concurrently via
    ``asyncio.gather``; each ``asetup`` sees the *initial* ctx (not prior
    binds), so use only when the fleet's items don't cross-depend. Async
    only; the sync ``_open`` ignores it. Teardown stays LIFO regardless.
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

    def __repr__(self) -> str:
        cls = self._payload["cls"]
        keys = list(self._payload["specs"].keys())
        return f"ProvideDict({cls.__name__}, keys={keys!r})"


# =========================================================================
# With - N-ary bracket sequencer
# =========================================================================


class With(_LifecycleBracket):
    """Sequence N lifecycle brackets: enter in order, LIFO teardown.

    Same shape as Python's ``with A, B, C: body`` -- each bracket's ``_open``
    is entered in order, ctx accumulates across them, ``body`` runs against
    the final ctx, teardown fires in reverse on exit. If any bracket's setup
    raises, already-entered brackets tear down in reverse before propagating.

    Eliminates the outer ``Provide(a, kw, Provide(b, kw, Provide(c, kw, body)))``
    nesting cascade when stacking many peers at one level::

        With(
            Provide(RayCluster, {...}),
            Provide(RayService, {...}, tag="A"),
            Provide(RayService, {...}, tag="B"),
            ProvideDict(RayService, {...}),
            body=feed,
        )

    Composes any ``_LifecycleBracket``: ``Provide``, ``ProvideList``,
    ``ProvideDict``, ``InvisiblesProxy``, ... Each bracket is used as a SPEC
    (its own ``body`` slot is ignored -- ``With`` re-enters its ``_open`` /
    ``_aopen`` to accumulate ctx).
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

