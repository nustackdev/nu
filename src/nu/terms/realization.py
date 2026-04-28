"""Realization algebra - scalar/stream + 2x2 edge matrix + four-method API.

Each value-producing Nu yields in one of two shapes: scalar (one value)
or stream (0..N values). The 2x2 edge matrix decides what happens when a
consumer asks a producer for values (see
projects/nu/model/04-laws/04-realization-algebra.md):

```
              producer
              scalar       stream
consumer
scalar        DIRECT       REFUSED   <- bridged when consumer is Reduction
stream        LIFTED       PULLED
```

REFUSED is a hard error at composition time unless the consumer is a
`Reduction`. The validator is registered with `nu.py` at import.

Four-method API derivation: each kind ships its native pair; the protocol
fills the rest:

- ScalarProducer: native `eval` / `aeval`; `open` / `aopen` lifted to
  single-yield generator.
- StreamProducer: native `open` / `aopen`; scalar pair REFUSED unless
  wrapped in a Reduction.
- Sync ↔ async fill across `support`:
  - `{sync, async}` - kind ships both; nothing filled.
  - `{sync}` - sync only; async twin runs sync impl inline on the loop
    (with a one-time warning).
  - `{async}` - async only; sync twin unreachable per the top diamond -
    install a "raise" stub.

`four_method_pick(producer, exec_state)` returns the bound method to
call. The runtime calls this for every producer node.
"""

from __future__ import annotations

import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any

from .nu import NuBase, register_composition_validator, register_subclass_validator
from .query import Reduction
from .span import Span
from .types import ExecState, Mode, Realization


if TYPE_CHECKING:
    from collections.abc import Callable

    from .protocol import Nu


__all__ = [
    "EdgeMode",
    "edge_dispatch",
    "four_method_pick",
    "realization_of",
]


class EdgeMode(Enum):
    """The four cells of the realization matrix."""

    DIRECT = "direct"
    LIFTED = "lifted"
    PULLED = "pulled"
    REFUSED = "refused"


def realization_of(nu: Nu) -> Realization:
    """The native realization of a producer node.

    Span recurses into its body. Every other kind reads its class-level
    `realization`.
    """
    if isinstance(nu, Span):
        body = nu._children[type(nu).body_slot]
        return realization_of(body)
    real = getattr(type(nu), "realization", None)
    if isinstance(real, Realization):
        return real
    msg = f"{type(nu).__name__}: no realization declared"
    raise TypeError(msg)


_MATRIX: dict[tuple[Realization, Realization], EdgeMode] = {
    (Realization.SCALAR, Realization.SCALAR): EdgeMode.DIRECT,
    (Realization.SCALAR, Realization.STREAM): EdgeMode.REFUSED,
    (Realization.STREAM, Realization.SCALAR): EdgeMode.LIFTED,
    (Realization.STREAM, Realization.STREAM): EdgeMode.PULLED,
}


def edge_dispatch(consumer: Nu, producer: Nu) -> EdgeMode:
    """Decide the realization mode at the consumer<-producer edge.

    REFUSED is bridged to DIRECT when the consumer is a `Reduction`
    (First, Last, Collect, Reduce). Outside of that, REFUSED stands and
    a composition-time validator turns it into a hard error.
    """
    c = realization_of(consumer)
    p = realization_of(producer)
    shape = _MATRIX[(c, p)]
    if shape is EdgeMode.REFUSED and isinstance(consumer, Reduction):
        return EdgeMode.DIRECT
    return shape


def four_method_pick(producer: Nu, exec_state: ExecState) -> Callable[[Any], Any]:
    """Pick the bound method to call for a producer node.

    Realization picks scalar (`eval`/`aeval`) vs stream (`open`/`aopen`).
    `exec_state` picks the sync vs async twin.
    """
    real = realization_of(producer)
    if real is Realization.SCALAR:
        if exec_state is ExecState.LOOP:
            return producer.aeval
        return producer.eval
    if exec_state is ExecState.LOOP:
        return producer.aopen
    return producer.open


# --- composition-time validator: REFUSED edges ------------------------------


def _is_producer(nu: Any) -> bool:  # noqa: ANN401
    """A node has a realization iff it's a producer (Query / Ref / Span).

    For Span: only when its body is itself a producer (Span around a
    Command body has no realization edge to check).
    """
    real = getattr(type(nu), "realization", None)
    if isinstance(real, Realization):
        return True
    if isinstance(nu, Span):
        body_slot = getattr(type(nu), "body_slot", None)
        if body_slot is None or body_slot >= len(nu._children):
            return False
        return _is_producer(nu._children[body_slot])
    return False


def _validate_no_refused(nu: Any) -> None:  # noqa: ANN401
    """Composition-time check: no REFUSED producer/producer edge.

    Reduction children are exempt - they're the bridge.
    """
    if not _is_producer(nu):
        return
    for child in nu._children:
        if not _is_producer(child):
            continue
        mode = edge_dispatch(nu, child)
        if mode is EdgeMode.REFUSED:
            msg = (
                f"{type(nu).__name__} (scalar) cannot consume "
                f"{type(child).__name__} (stream): no canonical reduction. "
                "Wrap the stream child in a Reduction (First, Last, "
                "Collect, Reduce)."
            )
            raise TypeError(msg)


register_composition_validator(_validate_no_refused)


# --- four-method protocol fill ----------------------------------------------
#
# Sync<->async fill is wired off `support`:
#
# - `{sync, async}` - native ships both halves; nothing filled.
# - `{sync}`        - async twin runs sync impl inline on the loop, with
#                     a one-time warning.
# - `{async}`       - sync twin unreachable; install a stub that raises.
#
# Scalar->stream lift (single-yield) is left to the runtime caller. The
# native methods are picked by `four_method_pick`; the lift happens at
# the call site only when needed (a stream consumer asks a scalar
# producer for values).


def _install_sync_async_fill(cls: type) -> None:
    """Bind missing sync/async twin methods per `support`.

    Run as a class-init hook on EvalAtom subclasses.
    """
    support = getattr(cls, "support", None)
    if not isinstance(support, frozenset):
        return
    real = getattr(cls, "realization", None)
    if isinstance(real, Realization):
        if real is Realization.SCALAR:
            sync_name, async_name = "eval", "aeval"
        else:
            sync_name, async_name = "open", "aopen"
    elif _has_run_pair(cls):
        sync_name, async_name = "run", "arun"
    else:
        return

    if support == frozenset({Mode.SYNC, Mode.ASYNC}):
        return  # both halves expected; let validators handle missing.
    if support == frozenset({Mode.SYNC}):
        if async_name not in cls.__dict__:
            _bind_sync_only_async_twin(cls, sync_name, async_name)
        return
    if support == frozenset({Mode.ASYNC}):
        if sync_name not in cls.__dict__:
            _bind_async_only_sync_twin(cls, sync_name)
        return


def _has_run_pair(cls: type) -> bool:
    return hasattr(cls, "run") and hasattr(cls, "arun")


def _bind_sync_only_async_twin(cls: type, sync_name: str, async_name: str) -> None:
    """Make the async twin run the sync impl inline. One-time warning."""
    if sync_name in ("eval", "open"):

        async def _async_twin(self: Any, ctx: Any, _sn: str = sync_name) -> Any:  # noqa: ANN401
            warnings.warn(
                f"{type(self).__name__} is support={{sync}}; running sync "
                f"impl inline on the loop. Consider declaring "
                f"support={{sync, async}} or using a {{async}} sibling.",
                RuntimeWarning,
                stacklevel=2,
            )
            return getattr(self, _sn)(ctx)

        async def _async_twin_open(self: Any, ctx: Any) -> Any:  # noqa: ANN401
            warnings.warn(
                f"{type(self).__name__} is support={{sync}}; running sync open inline on the loop.",
                RuntimeWarning,
                stacklevel=2,
            )
            for v in self.open(ctx):
                yield v

        if sync_name == "open":
            setattr(cls, async_name, _async_twin_open)
        else:
            setattr(cls, async_name, _async_twin)
    else:  # run / arun

        async def _async_run(self: Any, ctx: Any) -> None:  # noqa: ANN401
            warnings.warn(
                f"{type(self).__name__} is support={{sync}}; running sync run inline on the loop.",
                RuntimeWarning,
                stacklevel=2,
            )
            self.run(ctx)

        setattr(cls, async_name, _async_run)


def _bind_async_only_sync_twin(cls: type, sync_name: str) -> None:
    """Top diamond rules out reaching this; install a raising stub."""

    def _sync_stub(self: Any, *_: Any, **__: Any) -> Any:  # noqa: ANN401
        msg = (
            f"{type(self).__name__} is support={{async}}; the sync twin "
            "is unreachable per the top diamond. If you got here, the "
            "tree contains an async-only atom and the runtime should "
            "have switched to a loop."
        )
        raise RuntimeError(msg)

    setattr(cls, sync_name, _sync_stub)


register_subclass_validator(NuBase, _install_sync_async_fill)
