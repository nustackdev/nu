"""``Provide`` brackets: construct + bind fabrics for the body's duration.

The tree carries a *class* plus a *spec* (kwargs, list of kwargs, or dict of
kwargs). On entry each bracket constructs its fabric(s), runs setup, binds on
ctx. On exit teardown fires in reverse (LIFO), so an outer fabric is still
live while inner ones tear down.

Three primitives, one per attach shape:

    Provide(cls, kwargs, body, *, tag=None)
        # bind ONE instance keyed by (cls, tag)

    ProvideList(cls, [kwargs_a, kwargs_b, ...], body)
        # bind N instances keyed by (cls, 0), (cls, 1), ...

    ProvideDict(cls, {"k1": kwargs_a, "k2": kwargs_b}, body)
        # bind N instances keyed by (cls, "k1"), (cls, "k2"), ...

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

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from nu.spans.bracket import _LifecycleBracket


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.runtime import Context


__all__ = ["Provide", "ProvideDict", "ProvideList"]


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


# =========================================================================
# Provide - one instance
# =========================================================================


class Provide(_LifecycleBracket):
    """Construct ONE resource of ``cls(**kwargs)``, bind on ctx by tag.

    On entry:
        - instance = cls(**kwargs)
        - if instance has setup / asetup, call it (async run prefers asetup)
        - ctx.bind(cls, instance, tag) if tag given, else ctx.bind(cls, instance)
    On exit:
        - cleanup / acleanup (if defined)
    """

    def __init__(
        self,
        cls: type,
        kwargs: Mapping[str, object] | None = None,
        body: Nu | None = None,
        *,
        tag: object = None,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["kwargs"] = dict(kwargs or {})
        self._payload["tag"] = tag

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        kwargs = self._payload["kwargs"]
        tag = self._payload["tag"]
        tags = (tag,) if tag is not None else ()

        instance = _construct(cls, kwargs)
        setup_done: list[object] = []
        try:
            _setup(instance, ctx)
            setup_done.append(instance)
            yield ctx.bind(cls, instance, *tags)
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        cls = self._payload["cls"]
        kwargs = self._payload["kwargs"]
        tag = self._payload["tag"]
        tags = (tag,) if tag is not None else ()

        instance = _construct(cls, kwargs)
        setup_done: list[object] = []
        try:
            await _asetup(instance, ctx)
            setup_done.append(instance)
            yield ctx.bind(cls, instance, *tags)
        finally:
            await _ateardown(setup_done)

    def __repr__(self) -> str:
        cls = self._payload["cls"]
        tag = self._payload["tag"]
        tag_str = f", tag={tag!r}" if tag is not None else ""
        return f"Provide({cls.__name__}{tag_str})"


# =========================================================================
# ProvideList - N instances by index
# =========================================================================


class ProvideList(_LifecycleBracket):
    """Construct N resources of ``cls``, bind each on ctx at index tags 0..N-1.

    ``specs`` is a list of kwargs dicts, one per instance. Setup runs in
    order; teardown in reverse. If any setup raises, already-setup instances
    are torn down in reverse before propagating.
    """

    def __init__(
        self,
        cls: type,
        specs: Sequence[Mapping[str, object]],
        body: Nu | None = None,
        *,
        base_tag: int = 0,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["specs"] = [dict(s) for s in specs]
        self._payload["base_tag"] = base_tag

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        specs = self._payload["specs"]
        base = self._payload["base_tag"]

        setup_done: list[object] = []
        try:
            for i, kwargs in enumerate(specs):
                inst = _construct(cls, kwargs)
                _setup(inst, ctx)
                setup_done.append(inst)
                ctx = ctx.bind(cls, inst, base + i)
            yield ctx
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        cls = self._payload["cls"]
        specs = self._payload["specs"]
        base = self._payload["base_tag"]

        setup_done: list[object] = []
        try:
            for i, kwargs in enumerate(specs):
                inst = _construct(cls, kwargs)
                await _asetup(inst, ctx)
                setup_done.append(inst)
                ctx = ctx.bind(cls, inst, base + i)
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
    """

    def __init__(
        self,
        cls: type,
        specs: Mapping[object, Mapping[str, object]],
        body: Nu | None = None,
    ) -> None:
        super().__init__(body)
        self._payload["cls"] = cls
        self._payload["specs"] = {k: dict(v) for k, v in specs.items()}

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        cls = self._payload["cls"]
        specs = self._payload["specs"]

        setup_done: list[object] = []
        try:
            for key, kwargs in specs.items():
                inst = _construct(cls, kwargs)
                _setup(inst, ctx)
                setup_done.append(inst)
                ctx = ctx.bind(cls, inst, key)
            yield ctx
        finally:
            _teardown(setup_done)

    @asynccontextmanager
    async def _aopen(self, ctx: Context) -> AsyncIterator[Context]:
        cls = self._payload["cls"]
        specs = self._payload["specs"]

        setup_done: list[object] = []
        try:
            for key, kwargs in specs.items():
                inst = _construct(cls, kwargs)
                await _asetup(inst, ctx)
                setup_done.append(inst)
                ctx = ctx.bind(cls, inst, key)
            yield ctx
        finally:
            await _ateardown(setup_done)

    def __repr__(self) -> str:
        cls = self._payload["cls"]
        keys = list(self._payload["specs"].keys())
        return f"ProvideDict({cls.__name__}, keys={keys!r})"
