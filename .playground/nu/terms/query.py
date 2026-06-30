"""Query, ScalarQuery, StreamQuery, Reduction - abstract Query bases.

Queries yield value(s); their effects ⊆ {RESOLVE, READ}. Class-time
validator forbids WRITE in `own_effects`.

ScalarQuery wraps `eval` / `aeval` with sentinel propagation: if any
operand is a sentinel and `accepts_sentinels` is False, return INVALID
without invoking `_apply` / `_aapply`. StreamQuery does NOT auto-collapse
- sentinels in a stream are ordinary values for the consumer.

Reduction is a base class (not a flag): subclasses inheriting Reduction
opt the SCALAR/STREAM edge into DIRECT.

Concrete Query atoms (Literal, First, Last, Collect, Reduce) live in
`nu.queries`.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .effects import own_tracked_effects
from .interaction import Interaction
from .nu import register_subclass_validator
from .sentinels import INVALID, is_sentinel
from .types import Effect, Realization


__all__ = [
    "Query",
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


class Reduction(ScalarQuery):
    """Scalar Query whose child is a StreamQuery.

    Opts the SCALAR/STREAM edge into DIRECT (handled in
    `realization.py`). Concrete reductions (First, Last, Collect, Reduce)
    live in `nu.queries.reduction` and inherit from here. They override
    `eval` / `aeval` directly (NOT `_apply`) and drive their child's
    stream via `child.open(ctx)` / `child.aopen(ctx)`.
    """


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
