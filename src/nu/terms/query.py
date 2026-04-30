"""Query, ScalarQuery, StreamQuery, Literal, Reduction.

Queries yield value(s); their effects ⊆ {RESOLVE, READ}. Class-time
validator forbids WRITE in `own_effects`.

ScalarQuery wraps `eval` / `aeval` with sentinel propagation: if any
operand is a sentinel and `accepts_sentinels` is False, return INVALID
without invoking `_apply` / `_aapply`. StreamQuery does NOT auto-collapse
- sentinels in a stream are ordinary values for the consumer.

Reduction is a base class (not a flag): subclasses inheriting Reduction
opt the SCALAR/STREAM edge into DIRECT (Phase D' wires that).
"""

from __future__ import annotations

from typing import Any, ClassVar

from .effects import own_tracked_effects
from .interaction import Interaction
from .nu import register_subclass_validator
from .sentinels import INVALID, is_sentinel
from .types import Effect, Realization


__all__ = [
    "Collect",
    "First",
    "Last",
    "Literal",
    "Query",
    "Reduce",
    "Reduction",
    "ScalarQuery",
    "StreamQuery",
]


class Query(Interaction):
    """Abstract Query base. Subtree effects ⊆ {RESOLVE, READ}."""


class ScalarQuery(Query):
    """Single-value Query.

    Concrete subclasses override `_apply` / `_aapply`. `eval` / `aeval`
    are wrapped here: open each child, take its first value, propagate
    sentinels, then call `_apply`.

    Native pair: `eval` / `aeval`. The stream pair (`open` / `aopen`) is
    derived per protocol (single-yield generator) by `realization.py`.
    """

    realization: ClassVar[Realization] = Realization.SCALAR
    accepts_sentinels: ClassVar[bool] = False

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        ops = [_child_eval(c, ctx) for c in self._children]
        if not self.accepts_sentinels and any(is_sentinel(o) for o in ops):
            return INVALID
        return self._apply(ctx, ops)

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        ops = [await _child_aeval(c, ctx) for c in self._children]
        if not self.accepts_sentinels and any(is_sentinel(o) for o in ops):
            return INVALID
        return await self._aapply(ctx, ops)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        """Compute the scalar result from operands. Override per kind."""
        msg = f"{type(self).__name__}._apply - override on the concrete kind"
        raise NotImplementedError(msg)

    async def _aapply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        """Async variant of `_apply`. Default delegates to `_apply`."""
        return self._apply(ctx, ops)


class StreamQuery(Query):
    """N-value Query. Native pair: `open` / `aopen`.

    Concrete subclasses override `open` / `aopen` directly. The scalar
    pair is REFUSED unless wrapped in a Reduction.
    """

    realization: ClassVar[Realization] = Realization.STREAM

    def open(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.open - phase D"
        raise NotImplementedError(msg)

    def aopen(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.aopen - phase D"
        raise NotImplementedError(msg)


class Literal(ScalarQuery):
    """Pure leaf. Holds a value, evaluates to it.

    No operands; exempt from the sentinel-propagation wrap by virtue of
    zero operands.
    """

    accepts_sentinels: ClassVar[bool] = True
    _value: object

    def __init__(self, value: object) -> None:
        super().__init__()
        self._value = value

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._value

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._value

    def __repr__(self) -> str:
        return f"Literal({self._value!r})"


class Reduction(ScalarQuery):
    """Scalar Query whose child is a StreamQuery.

    Opts the SCALAR/STREAM edge into DIRECT (handled in
    `realization.py`). Concrete reductions (First, Last, Collect, Reduce)
    inherit from here.

    Concrete reductions override `eval` / `aeval` directly (NOT `_apply`)
    and drive their child's stream via `child.open(ctx)` / `child.aopen(ctx)`.
    """


# --- concrete reductions ----------------------------------------------------


from .types import Mode  # noqa: E402


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class First(Reduction):
    """First yield of the child stream. EMPTY if the stream is empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from .sentinels import EMPTY

        child = self._children[0]
        for v in child.open(ctx):
            return v
        return EMPTY

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from .sentinels import EMPTY

        child = self._children[0]
        async for v in child.aopen(ctx):
            return v
        return EMPTY


class Last(Reduction):
    """Last yield of the child stream. EMPTY if the stream is empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from .sentinels import EMPTY

        child = self._children[0]
        found = False
        last: Any = None
        for v in child.open(ctx):
            last = v
            found = True
        return last if found else EMPTY

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        from .sentinels import EMPTY

        child = self._children[0]
        found = False
        last: Any = None
        async for v in child.aopen(ctx):
            last = v
            found = True
        return last if found else EMPTY


class Collect(Reduction):
    """Drain the child stream into a list."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def eval(self, ctx: Any) -> list[Any]:  # noqa: D102
        return list(self._children[0].open(ctx))

    async def aeval(self, ctx: Any) -> list[Any]:  # noqa: D102
        out: list[Any] = []
        async for v in self._children[0].aopen(ctx):
            out.append(v)
        return out


class Reduce(Reduction):
    """Fold the child stream with a Python callable.

    `Reduce(stream_q, fn, initial=...)` - fn is plain callable, not a Nu.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        stream: Any,  # noqa: ANN401
        fn: Any,  # noqa: ANN401
        initial: Any = None,  # noqa: ANN401
    ) -> None:
        # Only `stream` is a Nu child; fn / initial are plain values stored
        # on the instance.
        super().__init__(stream)
        self._fn = fn
        self._initial = initial

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        acc = self._initial
        for v in self._children[0].open(ctx):
            acc = self._fn(acc, v)
        return acc

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        acc = self._initial
        async for v in self._children[0].aopen(ctx):
            acc = self._fn(acc, v)
        return acc


# --- helpers -----------------------------------------------------------------


def _child_eval(child: Any, ctx: Any) -> Any:  # noqa: ANN401
    """Open a child for a single value (sync)."""
    eval_fn = getattr(child, "eval", None)
    if eval_fn is not None:
        return eval_fn(ctx)
    msg = f"{type(child).__name__} cannot be eval'd in scalar position"
    raise TypeError(msg)


async def _child_aeval(child: Any, ctx: Any) -> Any:  # noqa: ANN401
    """Open a child for a single value (async)."""
    aeval_fn = getattr(child, "aeval", None)
    if aeval_fn is not None:
        return await aeval_fn(ctx)
    msg = f"{type(child).__name__} cannot be aeval'd in scalar position"
    raise TypeError(msg)


# --- subclass validator ------------------------------------------------------


def _validate_query(cls: type) -> None:
    """Queries must not declare WRITE in `own_effects`."""
    own = getattr(cls, "own_effects", {})
    for slot, eff in own.items():
        effs = eff if isinstance(eff, frozenset) else {eff}
        if Effect.WRITE in effs:
            msg = (
                f"{cls.__module__}.{cls.__qualname__}: Query kinds cannot "
                f"declare WRITE in own_effects (slot {slot} has {eff!r}). "
                "Use a Command kind for write effects."
            )
            raise TypeError(msg)


register_subclass_validator(Query, _validate_query)


# --- composition validator: Query subtree effects ⊆ {RESOLVE, READ} ----------


def _validate_query_subtree(nu: Any) -> None:  # noqa: ANN401
    """If the atom is a Query, none of its own tracked effects may be WRITE.

    Subtree-level enforcement also follows because every descendant Query
    re-runs this check at its own __init__.
    """
    if not isinstance(nu, Query):
        return
    for _ref, eff in own_tracked_effects(nu):
        if eff is Effect.WRITE:
            msg = (
                f"{type(nu).__name__}: Query atom carries WRITE effect "
                f"(via own_effects or child binding). Queries are read-only."
            )
            raise TypeError(msg)


# Register at import so NuBase.__init__ picks it up.
from .nu import register_composition_validator as _register_comp  # noqa: E402


_register_comp(_validate_query_subtree)
