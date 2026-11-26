"""``Provide`` brackets: construct + bind fabrics for the body's duration.

The tree carries a *class* plus a *spec* (kwargs, list of kwargs, or dict of
kwargs) as config children after the body (see ``nu.Bracket``).
Every config value is a child: a plain value becomes its Literal, a term is
kept as given, and a spec given as a mapping (or a list or mapping of them)
is built field by field, so any single field, tag or option can be computed
or read from a store. On entry each bracket evaluates them, constructs its
fabric(s), runs setup, binds on ctx. On exit teardown fires in reverse (LIFO), so an outer fabric is still
live while inner ones tear down.

Three primitives, one per attach shape:

    Provide(cls, *, args=(), kwargs=None, body=None, tag=None, tags=(), predicate=None)
        # bind ONE instance keyed by (cls, *tags)

    ProvideList(cls, *, specs=[kwargs_a, kwargs_b, ...], body=body,
                base_tag=0, extra_tags=(), predicate=None)
        # bind N instances at (cls, base_tag+0, *extra_tags), ...

    ProvideDict(cls, *, specs={"k1": kwargs_a, ...}, body=body,
                extra_tags=(), predicate=None)
        # bind N instances at (cls, "k1", *extra_tags), ...

Tag knobs (all optional, they compose):

- ``tag=`` on ``Provide`` is sugar for a single-tag ``tags=(tag,)``.
- ``tags=`` binds under an unordered set of tags; ``ctx.get(cls, t)`` matches
  when ``t`` is a subset of the bound set (specificity fallback).
- ``predicate=`` is a single guard callable forwarded to the Context as a
  guard: ``ctx.get(cls, *tags, **data)`` resolves this binding only when
  ``predicate(**data)`` returns True. Useful for "bind a Navigator whose
  shard covers this address" without pre-computing all shard tags.

The ecosystem is open: ``ProvideSharded``, ``ProvideRoundRobin``,
``ProvideReplicated``, ``ProvideLazy``, etc. all follow the same shape - each
is a ``nu.Bracket`` subclass that overrides ``_open`` / ``_aopen`` (no-ops on
the base); the engine sees them as regular lifecycle spans.

Any class can be provided; the lifecycle follows from what the instance is:

- a ``nu.Fabric`` runs its hooks: ``setup`` / ``cleanup`` under the sync
  runtime, ``asetup`` / ``acleanup`` (which default to the sync pair) under
  the async one;
- a context manager is entered and exited, the async protocol first under
  the async runtime, and its ``__exit__`` sees the body's error;
- anything else has no lifecycle: it is bound on entry and unbound on exit.

A class given directly is checked when the bracket is built, a computed one
when it opens. The sync runtime refuses, before constructing it, a fabric
marked ``async_only``, one that overrides only the async half of its
lifecycle, and an async-only context manager.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, cast

from nu.lang import Bracket
from nu.lang.nu import Nu

from .fabric import Fabric


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator, Mapping, Sequence

    from nu.lang.runtime import Context


__all__ = ["Provide", "ProvideDict", "ProvideList", "With"]


# =========================================================================
# construction / lifecycle helpers
# =========================================================================


def _construct(cls: type, args: Sequence[object], kwargs: Mapping[str, object]) -> object:
    """Build one instance from ``cls(*args, **kwargs)``."""
    return cls(*args, **kwargs)


def _require_class(cls: object, bracket: str) -> type:
    """Refuse anything that is not a class.

    Run at build time when the class is given as a plain value, and again when
    the bracket opens, which is the first time a computed class is known.
    ``bracket`` is the refusing bracket's class name, so the message names
    ``ProvideList`` / ``ProvideDict`` / a subclass rather than ``Provide``.
    """
    if not isinstance(cls, type):
        name = getattr(cls, "__qualname__", None) or repr(cls)
        msg = f"{bracket} takes a class, got {name}"
        raise TypeError(msg)
    return cls


def _overrides(cls: type[Fabric], name: str) -> bool:
    """Whether ``cls`` replaces the ``Fabric`` default of lifecycle method ``name``."""
    return getattr(cls, name) is not getattr(Fabric, name)


def _is_cm(obj: object) -> bool:
    """Whether ``obj`` (an instance or a class) is a sync context manager."""
    kind = obj if isinstance(obj, type) else type(obj)
    return hasattr(kind, "__enter__") and hasattr(kind, "__exit__")


def _is_acm(obj: object) -> bool:
    """Whether ``obj`` (an instance or a class) is an async context manager."""
    kind = obj if isinstance(obj, type) else type(obj)
    return hasattr(kind, "__aenter__") and hasattr(kind, "__aexit__")


def _refuse_async_only(cls: type) -> None:
    """Sync path guard: refuse a class whose lifecycle the sync runner cannot drive.

    Called before instance construction so a mis-provisioned tree fails at
    the leaf ``Provide`` with a clear message, instead of half-building an
    instance whose async setup we can't drive. Refused: a fabric marked
    ``async_only``; one that overrides ``asetup`` (or ``acleanup``) while
    keeping the no-op sync twin, which would otherwise run under ``nu.run``
    with its lifecycle silently skipped; and an async-only context manager.
    """
    if issubclass(cls, Fabric):
        if cls.async_only:
            msg = f"{cls.__name__} requires the async runner (nu.arun); it is async_only"
            raise RuntimeError(msg)
        for sync, aio in (("setup", "asetup"), ("cleanup", "acleanup")):
            if _overrides(cls, aio) and not _overrides(cls, sync):
                msg = f"{cls.__name__} has no sync {sync}; use nu.arun or add {sync}()"
                raise RuntimeError(msg)
    elif _is_acm(cls) and not _is_cm(cls):
        msg = f"{cls.__name__} is an async context manager; use nu.arun"
        raise RuntimeError(msg)


def _sync_class(cls: object, bracket: str) -> type:
    """The class a sync open constructs: one the sync runner can drive."""
    kind = _require_class(cls, bracket)
    _refuse_async_only(kind)
    return kind


def _async_class(cls: object, bracket: str) -> type:
    """The class an async open constructs: any class."""
    return _require_class(cls, bracket)


class _Life:
    """One provided instance's lifecycle, picked by what the instance is.

    A ``Fabric`` runs its own hooks (``setup`` / ``cleanup``, or the async
    pair). A context manager is entered and exited, with the body's error
    handed to ``__exit__``. Anything else has no lifecycle: it is only bound
    and unbound. ``Fabric`` wins over a context manager when a class is both.
    """

    __slots__ = ("inst",)

    def __init__(self, inst: object) -> None:
        self.inst = inst

    def setup(self, ctx: Context) -> None:
        inst = self.inst
        if isinstance(inst, Fabric):
            inst.setup(ctx)
        elif _is_cm(inst):
            inst.__enter__()  # type: ignore[attr-defined]

    def teardown(self, exc: BaseException | None) -> None:
        inst = self.inst
        if isinstance(inst, Fabric):
            inst.cleanup()
        elif _is_cm(inst):
            # The return value is ignored: a provided resource never swallows
            # the body's error.
            inst.__exit__(*_exc_info(exc))  # type: ignore[attr-defined]

    async def asetup(self, ctx: Context) -> None:
        inst = self.inst
        if isinstance(inst, Fabric):
            await inst.asetup(ctx)
        elif _is_acm(inst):
            await inst.__aenter__()  # type: ignore[attr-defined]
        elif _is_cm(inst):
            inst.__enter__()  # type: ignore[attr-defined]

    async def ateardown(self, exc: BaseException | None) -> None:
        inst = self.inst
        if isinstance(inst, Fabric):
            await inst.acleanup()
        elif _is_acm(inst):
            await inst.__aexit__(*_exc_info(exc))  # type: ignore[attr-defined]
        elif _is_cm(inst):
            inst.__exit__(*_exc_info(exc))  # type: ignore[attr-defined]


def _exc_info(exc: BaseException | None) -> tuple[object, object, object]:
    """The ``(type, value, traceback)`` triple ``__exit__`` takes."""
    if exc is None:
        return None, None, None
    return type(exc), exc, exc.__traceback__


@contextmanager
def _torn_down(lives: list[_Life]) -> Iterator[None]:
    """Tear ``lives`` down in reverse on exit, handing each the body's error."""
    try:
        yield
    except BaseException as exc:
        for life in reversed(lives):
            life.teardown(exc)
        raise
    for life in reversed(lives):
        life.teardown(None)


@asynccontextmanager
async def _atorn_down(lives: list[_Life]) -> AsyncIterator[None]:
    """Async sibling of :func:`_torn_down`."""
    try:
        yield
    except BaseException as exc:
        for life in reversed(lives):
            await life.ateardown(exc)
        raise
    for life in reversed(lives):
        await life.ateardown(None)


def _merge_tags(tag: object, tags: Sequence[object]) -> tuple[object, ...]:
    """Fold ``tag=`` sugar + ``tags=`` seq into one positional tuple."""
    seq = tuple(tags)
    return seq if tag is None else (tag, *seq)


def _forms() -> tuple[Callable[..., Nu], Callable[..., Nu], Callable[..., Nu]]:
    """The ``DictOf``, ``ListOf`` and ``TupleOf`` atoms config specs are built from.

    Lazy: the forms package sits above this one.
    """
    from nu.forms.collections_interactions import DictOf, ListOf, TupleOf

    return cast(
        "tuple[Callable[..., Nu], Callable[..., Nu], Callable[..., Nu]]", (DictOf, ListOf, TupleOf)
    )


def _kwargs_child(kwargs: Mapping[str, object] | Nu | None) -> Nu:
    """A kwargs child: a term stays as given, a mapping is built from its fields.

    Each field is its own child, so one field can be computed while the rest
    stay plain. None gives the empty mapping.
    """
    if isinstance(kwargs, Nu):
        return kwargs
    dict_of, _, _ = _forms()
    return dict_of(**(kwargs or {}))


def _tuple_child(items: Sequence[object] | Nu) -> Nu:
    """A tag tuple child: a term stays as given, else each item is its own child."""
    if isinstance(items, Nu):
        return items
    _, _, tuple_of = _forms()
    return tuple_of(*items)


def _list_specs_child(specs: Sequence[Mapping[str, object] | Nu] | Nu) -> Nu:
    """ProvideList specs: a term stays as given, else a list of kwargs children."""
    if isinstance(specs, Nu):
        return specs
    _, list_of, _ = _forms()
    return list_of(*(_kwargs_child(s) for s in specs))


def _dict_specs_child(specs: Mapping[object, Mapping[str, object] | Nu] | Nu) -> Nu:
    """ProvideDict specs: a term stays as given, else a dict of key to kwargs children.

    Built from ``(key, kwargs)`` pairs, since a key is any tag, not only a str.
    """
    if isinstance(specs, Nu):
        return specs
    dict_of, list_of, tuple_of = _forms()
    return dict_of(list_of(*(tuple_of(k, _kwargs_child(v)) for k, v in specs.items())))


def _bind_key(cls: type, bind_as: type | None) -> type:
    """The type an instance binds under: ``bind_as``, else ``cls._nu_bind_as``, else ``cls``."""
    return bind_as or getattr(cls, "_nu_bind_as", None) or cls


def _bind(
    ctx: Context,
    cls: type,
    inst: object,
    tags: Sequence[object],
    predicate: Callable | None,
) -> Context:
    """``ctx`` with ``inst`` provided under ``cls`` + tags, optionally guarded."""
    if predicate is None:
        return ctx.bind(cls, inst, *tags)
    return ctx.bind(cls, inst, *tags, predicate=predicate)


# =========================================================================
# Provide - one instance
# =========================================================================


class Provide(Bracket):
    """Constructs one instance and binds it on the Context for the body's duration.

    This is how a stateful Nu program gets its state: nothing in the tree
    reaches a fabric that was not provided around it. On entry the bracket
    builds ``cls(*args, **kwargs)``, runs its setup if it has one, and binds
    the instance on the Context under the class plus any tags. The body runs
    against that Context. On exit teardown fires, and it fires in reverse
    order across nested brackets, so an outer fabric is still live while the
    ones inside it are tearing down.

    Args:
        cls: the class to construct, any class. Also the key it binds
            under, unless ``bind_as`` or the class's own ``_nu_bind_as``
            overrides that.
        kwargs: passed straight to the constructor. A mapping whose values
            may each be a term, or a term that yields the whole mapping
            (computed, or read from a store); evaluated on entry.
        body: the tree that runs with the fabric bound.

    Notes:
        - Every config value is a child, so any of them can be computed: a
          term given for ``cls``, a tag, ``predicate``, ``bind_as``, the
          whole kwargs or one kwargs value is evaluated on entry. A term the
          fabric should receive as data (a worker's ``init`` bracket) is
          quoted: ``{"init": nu.Literal(bracket)}``.
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
        - ``args=`` are positional constructor arguments, passed before
          ``kwargs``; each may be a term.
        - The lifecycle follows from what the instance is. A ``nu.Fabric``
          runs its hooks, which all default to no-ops, so it overrides only
          what it needs and its ``setup`` sees the outer Context. A context
          manager is entered and exited, and its ``__exit__`` gets the body's
          error; its return value is ignored, so the error always
          propagates. Anything else is only bound and unbound, which is how
          a plain ``dict`` lands on the Context fresh for each entry.
        - ``cls`` must be a class. One given directly is checked here, a
          computed one when the bracket opens; anything else raises
          ``TypeError``.
        - Under ``nu.arun`` the bracket calls ``asetup`` / ``acleanup``,
          which default to the sync pair; under ``nu.run`` it calls
          ``setup`` / ``cleanup``, and a fabric marked ``async_only``, or
          one overriding ``asetup`` / ``acleanup`` without the sync twin, is
          refused before it is even constructed.
        - Teardown only reaches instances whose setup completed, so a setup
          that raises does not leave a half-open fabric to be cleaned up.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket. For a stream body the fabric stays bound for the
        whole drain and tears down when the stream is exhausted.

    Example:
        >>> class Counter(nu.Fabric):
        ...     def __init__(self, start=0):
        ...         self.n = start
        >>> nu.run(nu.Provide(Counter, kwargs={"start": 5}, body=nu.FabricRef(Counter).exists()))[0]
        True
        >>> nu.run(nu.Provide(dict, kwargs={"n": 1}, body=nu.FabricRef(dict)))[0]
        {'n': 1}
    """

    def __init__(
        self,
        cls: type | Nu,
        *,
        args: Sequence[object] | Nu = (),
        kwargs: Mapping[str, object] | Nu | None = None,
        body: Nu | None = None,
        tag: object = None,
        tags: Sequence[object] = (),
        predicate: Callable | Nu | None = None,
        bind_as: type | Nu | None = None,
    ) -> None:
        if not isinstance(cls, Nu):
            _require_class(cls, type(self).__name__)
        # Children: [body, cls, args, kwargs, tags, predicate, bind_as].
        super().__init__(
            body,
            cls,
            _tuple_child(args),
            _kwargs_child(kwargs),
            _tuple_child(_merge_tags(tag, tags)),
            predicate,
            bind_as,
        )

    @contextmanager
    def _open(
        self,
        ctx: Context,
        cls: type,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        tags: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
    ) -> Iterator[Context]:
        cls = _sync_class(cls, type(self).__name__)
        life = _Life(_construct(cls, args, kwargs))
        lives: list[_Life] = []
        with _torn_down(lives):
            life.setup(ctx)
            lives.append(life)
            yield _bind(ctx, _bind_key(cls, bind_as), life.inst, tags, predicate)

    @asynccontextmanager
    async def _aopen(
        self,
        ctx: Context,
        cls: type,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        tags: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
    ) -> AsyncIterator[Context]:
        cls = _async_class(cls, type(self).__name__)
        life = _Life(_construct(cls, args, kwargs))
        lives: list[_Life] = []
        async with _atorn_down(lives):
            await life.asetup(ctx)
            lives.append(life)
            yield _bind(ctx, _bind_key(cls, bind_as), life.inst, tags, predicate)


# =========================================================================
# ProvideList - N instances by index
# =========================================================================


class ProvideList(Bracket):
    """Constructs a fleet of one class and binds each member under its index.

    The list shape of :class:`Provide`: one instance per spec, bound at
    ``base_tag + i`` so the fleet is addressed by position. Each instance is
    constructed, set up and bound before the next one is built, so a later
    member's setup sees the earlier ones already on the Context.

    Args:
        cls: the class every member is constructed from, any class.
        specs: one kwargs mapping per instance, in the order they are built.
            A sequence (each mapping, or any of its values, may be a term),
            or a term that yields the whole sequence; evaluated on entry.
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
            specs=[{"port": 8000}, {"port": 8001}],
            body=feed,
            extra_tags=("ledger",),
        )
    """

    def __init__(
        self,
        cls: type | Nu,
        *,
        specs: Sequence[Mapping[str, object] | Nu] | Nu,
        body: Nu | None = None,
        base_tag: int | Nu = 0,
        extra_tags: Sequence[object] | Nu = (),
        predicate: Callable | Nu | None = None,
        bind_as: type | Nu | None = None,
    ) -> None:
        if not isinstance(cls, Nu):
            _require_class(cls, type(self).__name__)
        # Children: [body, cls, specs, base_tag, extra_tags, predicate, bind_as].
        super().__init__(
            body,
            cls,
            _list_specs_child(specs),
            base_tag,
            _tuple_child(extra_tags),
            predicate,
            bind_as,
        )

    @contextmanager
    def _open(
        self,
        ctx: Context,
        cls: type,
        specs: Sequence[Mapping[str, object]],
        base: int,
        extra: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
    ) -> Iterator[Context]:
        cls = _sync_class(cls, type(self).__name__)
        bind_as = _bind_key(cls, bind_as)
        lives: list[_Life] = []
        with _torn_down(lives):
            for i, kwargs in enumerate(specs):
                life = _Life(_construct(cls, (), kwargs))
                life.setup(ctx)
                lives.append(life)
                ctx = _bind(ctx, bind_as, life.inst, (base + i, *extra), predicate)
            yield ctx

    @asynccontextmanager
    async def _aopen(
        self,
        ctx: Context,
        cls: type,
        specs: Sequence[Mapping[str, object]],
        base: int,
        extra: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
    ) -> AsyncIterator[Context]:
        cls = _async_class(cls, type(self).__name__)
        bind_as = _bind_key(cls, bind_as)
        lives: list[_Life] = []
        async with _atorn_down(lives):
            for i, kwargs in enumerate(specs):
                life = _Life(_construct(cls, (), kwargs))
                await life.asetup(ctx)
                lives.append(life)
                ctx = _bind(ctx, bind_as, life.inst, (base + i, *extra), predicate)
            yield ctx


# =========================================================================
# ProvideDict - N instances by key
# =========================================================================


class ProvideDict(Bracket):
    """Constructs a fleet of one class and binds each member under its own key.

    The mapping shape of :class:`Provide`: same as :class:`ProvideList` but
    addressed by the caller's key rather than by position, which is what you
    want when the members are named rather than numbered.

    Args:
        cls: the class every member is constructed from, any class.
        specs: a mapping of key to kwargs. Each key becomes the tag its
            instance binds under. A mapping (each key, kwargs mapping or
            value may be a term), or a term that yields the whole mapping;
            evaluated on entry.
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
            specs={"ledger": {"port": 8000}, "index": {"port": 8001}},
            body=feed,
        )
    """

    def __init__(
        self,
        cls: type | Nu,
        *,
        specs: Mapping[object, Mapping[str, object] | Nu] | Nu,
        body: Nu | None = None,
        extra_tags: Sequence[object] | Nu = (),
        predicate: Callable | Nu | None = None,
        bind_as: type | Nu | None = None,
        parallel: bool | Nu = False,
    ) -> None:
        if not isinstance(cls, Nu):
            _require_class(cls, type(self).__name__)
        # Children: [body, cls, specs, extra_tags, predicate, bind_as, parallel].
        super().__init__(
            body,
            cls,
            _dict_specs_child(specs),
            _tuple_child(extra_tags),
            predicate,
            bind_as,
            parallel,
        )

    @contextmanager
    def _open(
        self,
        ctx: Context,
        cls: type,
        specs: Mapping[object, Mapping[str, object]],
        extra: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
        parallel: bool,
    ) -> Iterator[Context]:
        cls = _sync_class(cls, type(self).__name__)
        bind_as = _bind_key(cls, bind_as)
        lives: list[_Life] = []
        with _torn_down(lives):
            for key, kwargs in specs.items():
                life = _Life(_construct(cls, (), kwargs))
                life.setup(ctx)
                lives.append(life)
                ctx = _bind(ctx, bind_as, life.inst, (key, *extra), predicate)
            yield ctx

    @asynccontextmanager
    async def _aopen(
        self,
        ctx: Context,
        cls: type,
        specs: Mapping[object, Mapping[str, object]],
        extra: Sequence[object],
        predicate: Callable | None,
        bind_as: type | None,
        parallel: bool,
    ) -> AsyncIterator[Context]:
        cls = _async_class(cls, type(self).__name__)
        import asyncio

        from nu.core.flows.parallel._scheduling import _join_all

        bind_as = _bind_key(cls, bind_as)
        lives: list[_Life] = []
        async with _atorn_down(lives):
            if parallel:
                keyed = [(key, _Life(_construct(cls, (), kw))) for key, kw in specs.items()]
                tasks = [asyncio.ensure_future(life.asetup(ctx)) for _, life in keyed]
                # Not gather: a failed or cancelled setup must not leave
                # its siblings running, and every setup that did finish
                # is owed its teardown on the way out.
                try:
                    await _join_all(tasks)
                finally:
                    lives.extend(
                        life
                        for (_, life), t in zip(keyed, tasks, strict=True)
                        if t.done() and not t.cancelled() and t.exception() is None
                    )
                for key, life in keyed:
                    ctx = _bind(ctx, bind_as, life.inst, (key, *extra), predicate)
            else:
                for key, kwargs in specs.items():
                    life = _Life(_construct(cls, (), kwargs))
                    await life.asetup(ctx)
                    lives.append(life)
                    ctx = _bind(ctx, bind_as, life.inst, (key, *extra), predicate)
            yield ctx


# =========================================================================
# With - N-ary bracket sequencer
# =========================================================================


class With(Bracket):
    """Enters several lifecycle brackets around one body, tearing down in reverse.

    Python's ``with A, B, C: body``, in the tree. Each bracket is opened in
    order and each provides on the same Context, so a later bracket's setup
    sees everything the earlier ones bound. The body runs with all of them
    provided, and on exit teardown fires in reverse. What it buys is flatness:
    stacking peers at one level instead of writing the
    ``Provide(a, body=Provide(b, body=Provide(c, body=body)))`` cascade by hand.

    Args:
        *brackets: the lifecycle brackets to enter, in order.
        body: the tree that runs with all of them open.

    Notes:
        - ``With`` builds that cascade for you: its one child is the first
          bracket, whose body slot holds the second, and so on down to
          ``body``. Each bracket is a real node of the tree, so its config
          children are evaluated on entry and effects and laws see it.
        - Each bracket is used as a spec: ``With`` puts the next layer into
          its body slot, so a body passed to a nested bracket is replaced.
          The brackets given are not changed; the cascade holds variants.
        - Composes anything with the lifecycle shape - ``Provide``,
          ``ProvideList``, ``ProvideDict``, ``InvisiblesProxy``, another
          ``With`` and the rest.
        - A bracket whose setup raises unwinds the ones already entered
          before the error propagates.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Bracket.

    Example:
        nu.With(
            nu.Provide(RayCluster, kwargs={...}),
            nu.Provide(RayService, kwargs={...}, tag="A"),
            nu.Provide(RayService, kwargs={...}, tag="B"),
            nu.ProvideDict(RayService, specs={...}),
            body=feed,
        )
    """

    def __init__(
        self,
        *brackets: Bracket,
        body: Nu | None = None,
    ) -> None:
        inner: object = body
        for b in reversed(brackets):
            if not isinstance(b, Bracket):
                msg = f"With takes brackets, got {type(b).__name__}"
                raise TypeError(msg)
            inner = b._rebody(inner)
        super().__init__(inner)
        self.n_brackets = len(brackets)

    def _walk(self) -> tuple[tuple[Bracket, ...], object]:
        """The cascade's brackets, outermost first, and the body under the last."""
        layers: list[Bracket] = []
        node: object = self._children[0]
        for _ in range(self.n_brackets):
            layer = cast("Bracket", node)
            layers.append(layer)
            node = layer._inner()
        return tuple(layers), node

    @property
    def brackets(self) -> tuple[Bracket, ...]:
        """The brackets of the cascade, outermost first, as they sit in the tree."""
        return self._walk()[0]

    def _inner(self) -> object:
        return self._walk()[1]

    def _rebody(self, body: object) -> With:
        return With(*self.brackets, body=body)

    @contextmanager
    def _enter(self, ctx: Context) -> Iterator[Context]:
        with ExitStack() as stack:
            for b in self.brackets:
                ctx = stack.enter_context(b._enter(ctx))
            yield ctx

    @asynccontextmanager
    async def _aenter(self, ctx: Context) -> AsyncIterator[Context]:
        async with AsyncExitStack() as stack:
            for b in self.brackets:
                ctx = await stack.enter_async_context(b._aenter(ctx))
            yield ctx
