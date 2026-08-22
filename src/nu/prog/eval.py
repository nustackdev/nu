"""Eval: dynamic evaluation of a Nu term produced at runtime.

Eval is the escape hatch from the static compile-then-drive model. Its sole
child (the *carrier*) is a scalar-yielding Nu subtree that, when evaluated,
returns another Nu term. Eval compiles that inner term against the same
schema as the outer program, checks it against an optional *promise*, and
drives it inside the current Runtime.

Layered contract:

- Static composition matrix treats Eval as a *universal child* -- it slot-fits
  every parent row. The composition law cannot know what the carrier will
  produce, so we accept the placement statically and defer the discipline to:
- A promise on the Eval term, pinning any subset of ``{sort, cardinality,
  has_async_only_atom, has_sync_only_atom}``. Runtime dispatch validates the
  inner tree's actual attributes against each pinned field and raises with a
  targeted message on mismatch (see :mod:`nu.prog.eval_promise`).
- ``eval_carrier_is_scalar``: the one static law Eval adds. The carrier must
  itself yield a scalar (checked through Span transparency via
  ``CHILD_CARDINALITY``) so the runtime always gets exactly one Nu term per
  evaluation.

Gotchas:

- Eval is opaque to the static effect walk (``COMPOSITION_EFFECTS``). Consumers
  that need to gate on possible dynamic effects read ``HAS_DYNAMIC`` and
  handle the subtree conservatively (see ``is_pure``, ``program_mutates``,
  ``auto_flow_atomic``).
- Sync entry (``run``, ``eval``) driving an Eval whose inner tree turns out to
  hold an async-only atom raises deep in dispatch. Pin
  ``has_async_only_atom=False`` on the promise to surface it earlier.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.engine.structure import Declared
from nu.lang.attributes import Attr, Cardinality, Sort
from nu.lang.kinds import Interaction
from nu.lang.nu import Nu

from .eval_promise import PROMISE_FIELDS, PROMISE_KEY, EvalPromiseError, check_promise


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Eval"]


class Eval(Interaction):
    """Dynamic evaluation: run a Nu term produced by a carrier at runtime.

    The carrier is a scalar-yielding child whose value is the Nu term to
    evaluate. An optional promise pins attribute expectations on the inner
    tree; the runtime raises :class:`EvalPromiseError` on mismatch.

    Args:
        carrier: a Nu subtree that yields a Nu term when evaluated.
        promise: optional mapping over any subset of
            ``{"sort", "cardinality", "has_async_only_atom", "has_sync_only_atom"}``.
    """

    _sort = Declared(value=Sort.DYNAMIC, name="sort")
    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")

    def __init__(self, carrier: Nu, *, promise: dict[str, Any] | None = None) -> None:
        super().__init__(carrier)
        if promise is not None:
            unknown = set(promise) - PROMISE_FIELDS
            if unknown:
                msg = (
                    f"Eval promise has unknown field(s) {sorted(unknown)!r}; "
                    f"allowed: {sorted(PROMISE_FIELDS)!r}"
                )
                raise ValueError(msg)
            self._payload[PROMISE_KEY] = dict(promise)

    def _promise(self) -> dict[str, Any]:
        return self._payload.get(PROMISE_KEY) or {}

    def _resolve_inner(self, rt: Runtime, inner: object, promise: dict[str, Any]) -> object:
        """Compile ``inner``, validate against ``promise``, return the inner program."""
        if not isinstance(inner, Nu):
            msg = f"Eval carrier produced {type(inner).__name__}; expected a Nu term"
            raise EvalPromiseError(msg)
        from nu.engine.compilation import compile as _compile

        inner_program = _compile(inner, rt.program._schema)
        check_promise(inner_program, promise)
        return inner_program

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        promise = self._promise()
        _self = self

        def thunk(rt: Runtime) -> object:
            inner = children[0](rt) if children else None
            inner_program = _self._resolve_inner(rt, inner, promise)
            if inner_program.attrs[Attr.HAS_ASYNC_ONLY_ATOM][0]:
                msg = (
                    "Eval: inner tree holds an async-only atom under sync "
                    "dispatch; drive via `arun`/`aeval`, or pin "
                    "`has_async_only_atom=False` on the promise."
                )
                raise RuntimeError(msg)
            from nu.lang.runtime import Runtime as _Rt

            inner_rt = _Rt(inner_program, rt.ctx, budget=rt.budget)
            return inner_rt.eval()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        promise = self._promise()
        _self = self

        async def athunk(rt: Runtime) -> object:
            inner = await children[0](rt) if children else None
            inner_program = _self._resolve_inner(rt, inner, promise)
            # Placement check: if this Eval is placed on the event loop
            # (typical under Race/AnyN/ParallelAsync), a sync-only inner
            # tree cannot run there. Symmetrically, an off-loop Eval
            # cannot host an async-only inner.
            on_loop_col = rt.program.attrs.get(Attr.ON_LOOP)
            on_loop = bool(on_loop_col[nid]) if on_loop_col is not None else False
            if on_loop and inner_program.attrs[Attr.HAS_SYNC_ONLY_ATOM][0]:
                msg = (
                    "Eval: inner tree holds a sync-only atom but this Eval "
                    "is placed on the event loop (e.g. under Race/AnyN/"
                    "ParallelAsync). Move the Eval off the loop or drop "
                    "the sync-only placement."
                )
                raise RuntimeError(msg)
            if not on_loop and inner_program.attrs[Attr.HAS_ASYNC_ONLY_ATOM][0]:
                msg = (
                    "Eval: inner tree holds an async-only atom but this "
                    "Eval is placed off the event loop (e.g. under "
                    "ParallelThreaded). Move the Eval onto the loop."
                )
                raise RuntimeError(msg)
            from nu.lang.runtime import Runtime as _Rt

            inner_rt = _Rt(inner_program, rt.ctx, budget=rt.budget)
            return await inner_rt.aeval()

        return athunk
