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
    """Runs a Nu term the carrier produced at runtime.

    The carrier is evaluated like any other child and its value must be a Nu
    term. That term is compiled against the same schema as the outer program
    and driven in a nested Runtime that shares the outer ctx and budget, so
    the inner tree sees the same fabrics, the same bound resources and the
    same budget as the tree it was spliced into.

    This is the one place a Nu tree grows after compile time, so everything
    the static passes would have settled about the inner tree is deferred:
    to the promise, which is checked once the term is in hand, and to
    dispatch, which checks the sync/async placement.

    Args:
        carrier: a Nu subtree that yields a Nu term when evaluated.
        promise: expectations pinned on the inner tree, any subset of
            ``{"sort", "cardinality", "has_async_only_atom",
            "has_sync_only_atom"}``. An unknown key is a ``ValueError`` at
            construction.

    Notes:
        - The composition matrix treats an Eval as a universal child: it
          slot-fits every parent row, because no static pass can know what
          the carrier will produce.
        - ``eval_carrier_is_scalar`` is the one static law it adds. The
          carrier must resolve, through Span transparency, to a scalar
          yielder, so dispatch always gets exactly one term per evaluation.
        - A ``cardinality`` field on the promise is also what the parent
          slot-fits against: without one the Eval presents as SCALAR, so an
          Eval whose inner tree is a stream has to pin it to be placed
          where a stream is wanted.
        - A ``sort`` promise matches on subsort, not identity, so pinning an
          interior sort accepts any descendant of it.
        - The inner term is compiled on every evaluation. Nothing is cached,
          so an Eval inside a loop recompiles once per iteration.
        - Opaque to the static effect walk. Consumers that need to gate on
          possible dynamic effects read ``Attr.HAS_DYNAMIC`` and treat the
          subtree conservatively (``is_pure``, ``program_mutates``,
          ``auto_flow_atomic``).
        - A carrier that yields anything other than a Nu term raises
          ``EvalPromiseError``, the same error a contradicted promise does.
        - Under sync dispatch an inner tree holding an async-only atom
          raises ``RuntimeError`` at evaluation. Pin
          ``has_async_only_atom=False`` to surface it at the promise check
          instead, which names the axis rather than the dispatch hop.
        - Under async dispatch the placement has to agree with the inner
          tree: an Eval on the event loop (under ``Race``, ``AnyN``,
          ``ParallelAsync``) cannot host a sync-only inner tree, and one off
          the loop (under ``ParallelThreaded``) cannot host an async-only
          one. Either way it raises ``RuntimeError``.
        - Nothing the inner tree raises while running is caught here. Wrap
          the Eval in a ``TryCatch`` to keep a dynamic program's failure
          local to the subtree that ran it.

    Yields:
        Whatever the inner tree yields, unchanged. Eval adds no EMPTY or
        INVALID rule of its own, so a sentinel from the inner tree passes
        straight out.

    Example:
        >>> src = '''
        ... import nu
        ... def out():
        ...     return nu.Int(6) * nu.Int(7)
        ... '''
        >>> nu.run(nu.Eval(nu.LoadNu(src)))[0]
        42

        >>> nu.run(nu.Eval(nu.Literal(nu.Int(1) + nu.Int(2))))[0]
        3
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
