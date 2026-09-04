"""Eval: dynamic evaluation of Nu terms produced at runtime.

Covers the compile-side surface (HAS_DYNAMIC fold, composition matrix,
eval_carrier_is_scalar law, observability + is_pure gates) and the
runtime dispatch (happy path, promise mismatches,
sync-entry-with-async-only-inner, forced-mode Parallel + Eval).
"""

from __future__ import annotations

import pytest
from _support.dyn_carriers import ConstCarrier
from _support.law_terms import Brk, Cmd, FlowS, Q, R, Stream
from _support.laws import assert_fails, assert_passes, violations

from nu.core.flows import Parallel, ParallelAsync, ParallelThreaded
from nu.core.flows.parallel import AnyN, Race
from nu.engine.structure import Declared
from nu.engine.validation import ValidationError
from nu.lang import (
    Attr,
    Cardinality,
    ScalarQuery,
    Sort,
)
from nu.lang.helpers import arun, run
from nu.lang.helpers import compile as nu_compile
from nu.prog import Eval, EvalPromiseError


# --- HAS_DYNAMIC fold ---------------------------------------------------


def _attr(term, attr, path=()):
    program = nu_compile(term)
    nid = program.id_of[path]
    return program.attrs[attr][nid]


def test_has_dynamic_false_on_bare_query() -> None:
    assert _attr(Q(), Attr.HAS_DYNAMIC) is False


def test_has_dynamic_true_at_dyn_root() -> None:
    assert _attr(Eval(ConstCarrier(Q())), Attr.HAS_DYNAMIC) is True


def test_has_dynamic_folds_up_through_flow() -> None:
    tree = FlowS(Cmd(R()), Eval(ConstCarrier(Q())))
    assert _attr(tree, Attr.HAS_DYNAMIC) is True


def test_has_dynamic_folds_through_span() -> None:
    tree = Brk(Eval(ConstCarrier(Q())))
    assert _attr(tree, Attr.HAS_DYNAMIC) is True


def test_has_dynamic_true_at_nested_dyn() -> None:
    inner = Eval(ConstCarrier(Q()))
    tree = Eval(ConstCarrier(inner))
    assert _attr(tree, Attr.HAS_DYNAMIC) is True


# --- Composition matrix: Eval is universal ------------------------------


def test_dyn_slot_fits_as_value_child() -> None:
    # Q's row accepts a Eval (universal child).
    assert_passes(Q(Eval(ConstCarrier(Q()))))


def test_dyn_slot_fits_as_work_child_under_strategy() -> None:
    # Strategy's row is _WORK only; Eval joins via _UNIVERSAL.
    assert_passes(FlowS(Cmd(R()), Eval(ConstCarrier(Q()))))


def test_dyn_slot_fits_under_bracket() -> None:
    assert_passes(Brk(Eval(ConstCarrier(Q()))))


# --- Eval as parent: carrier must be scalar (through Span) --------------


def test_dyn_scalar_carrier_passes() -> None:
    assert_passes(Eval(Q()))


def test_dyn_scalar_carrier_through_bracket_passes() -> None:
    assert_passes(Eval(Brk(Q())))


def test_dyn_stream_carrier_fails() -> None:
    assert_fails(Eval(Stream()), "eval_carrier_is_scalar")


def test_dyn_command_carrier_fails_composition() -> None:
    # Cmd is not value-yielding; the matrix rejects it before the carrier law.
    fired = [v.law for v in violations(Eval(Cmd(R())))]
    assert "composition" in fired


# --- is_pure gate ------------------------------------------------------


def test_is_pure_returns_false_under_dyn() -> None:
    from nu.tree.effects import is_pure

    assert is_pure(Eval(ConstCarrier(Q()))) is False


def test_is_pure_returns_false_when_dyn_nested_inside_span() -> None:
    from nu.tree.effects import is_pure

    assert is_pure(Brk(Eval(ConstCarrier(Q())))) is False


# --- program_mutates warning silenced under Eval ------------------------


def test_program_mutates_silent_under_dyn() -> None:
    fired = [v for v in violations(Eval(ConstCarrier(Q()))) if v.law == "program_mutates"]
    assert not fired


def test_program_mutates_silent_when_dyn_is_a_flow_child() -> None:
    fired = [v for v in violations(FlowS(Eval(ConstCarrier(Q())))) if v.law == "program_mutates"]
    assert not fired


# --- Parallel-family placement laws over Eval ---------------------------


def test_smart_parallel_rejects_dyn_child() -> None:
    with pytest.raises(ValidationError) as exc:
        from nu.lang.helpers import validate

        validate(nu_compile(Parallel(Eval(ConstCarrier(Q())), Cmd(R()))))
    assert "no_dynamic_under_smart_parallel" in str(exc.value) or "smart Parallel" in str(exc.value)


def test_parallel_threaded_accepts_dyn_at_compile() -> None:
    from nu.lang.helpers import validate

    validate(nu_compile(ParallelThreaded(Eval(ConstCarrier(Q())))))


def test_parallel_async_accepts_dyn_at_compile() -> None:
    from nu.lang.helpers import validate

    validate(nu_compile(ParallelAsync(Eval(ConstCarrier(Q())))))


# --- Runtime dispatch: happy path ---------------------------------------


class _One(ScalarQuery):
    """A trivial ScalarQuery that yields the int 1 (for inner-Eval results)."""

    def _compile(self, nid, children):
        def thunk(rt):
            return 1

        return thunk

    def _acompile(self, nid, children):
        async def athunk(rt):
            return 1

        return athunk


def test_dyn_happy_path_sync() -> None:
    value, _ = run(Eval(ConstCarrier(_One())))
    assert value == 1


async def test_dyn_happy_path_async() -> None:
    value, _ = await arun(Eval(ConstCarrier(_One())))
    assert value == 1


# --- Runtime dispatch: carrier must produce a Nu term ------------------


class _NonNuCarrier(ScalarQuery):
    """A carrier that returns a plain int - not a Nu term."""

    def _compile(self, nid, children):
        def thunk(rt):
            return 42

        return thunk

    def _acompile(self, nid, children):
        async def athunk(rt):
            return 42

        return athunk


def test_dyn_carrier_producing_non_nu_raises() -> None:
    with pytest.raises(EvalPromiseError, match="expected a Nu term"):
        run(Eval(_NonNuCarrier()))


# --- Runtime dispatch: promise mismatch, per axis ----------------------


def test_eval_promise_sort_mismatch_raises() -> None:
    # Inner is a ScalarQuery; pin promise sort=SCALAR_ACTION -> mismatch.
    with pytest.raises(EvalPromiseError, match="promise mismatch on sort"):
        run(Eval(ConstCarrier(_One()), promise={"sort": Sort.SCALAR_ACTION}))


def test_eval_promise_cardinality_mismatch_raises() -> None:
    # Inner is a ScalarQuery (SCALAR); pin cardinality=STREAM -> mismatch.
    with pytest.raises(EvalPromiseError, match="promise mismatch on cardinality"):
        run(Eval(ConstCarrier(_One()), promise={"cardinality": Cardinality.STREAM}))


def test_eval_promise_has_async_only_atom_mismatch_raises() -> None:
    with pytest.raises(EvalPromiseError, match="promise mismatch on has_async_only_atom"):
        run(Eval(ConstCarrier(_One()), promise={"has_async_only_atom": True}))


def test_eval_promise_has_sync_only_atom_mismatch_raises() -> None:
    with pytest.raises(EvalPromiseError, match="promise mismatch on has_sync_only_atom"):
        run(Eval(ConstCarrier(_One()), promise={"has_sync_only_atom": True}))


def test_eval_promise_all_axes_pass_when_matched() -> None:
    value, _ = run(
        Eval(
            ConstCarrier(_One()),
            promise={
                "sort": Sort.SCALAR_QUERY,
                "cardinality": Cardinality.SCALAR,
                "has_async_only_atom": False,
                "has_sync_only_atom": False,
            },
        ),
    )
    assert value == 1


# --- Runtime dispatch: sync entry with async-only inner ----------------


class _AsyncOnlyLeaf(ScalarQuery):
    """A ScalarQuery declared async-only; folds into HAS_ASYNC_ONLY_ATOM."""

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid, children):
        def thunk(rt):
            return 2

        return thunk

    def _acompile(self, nid, children):
        async def athunk(rt):
            return 2

        return athunk


def test_dyn_sync_entry_with_async_only_inner_raises() -> None:
    with pytest.raises(RuntimeError, match="async-only atom under sync"):
        run(Eval(ConstCarrier(_AsyncOnlyLeaf())))


# --- Runtime dispatch: forced-mode Parallel + Eval mismatches ----------


async def test_parallel_threaded_over_dyn_with_async_only_inner_raises() -> None:
    tree = ParallelThreaded(Eval(ConstCarrier(_AsyncOnlyLeaf())))
    with pytest.raises(RuntimeError, match=r"async-only atom under sync"):
        await arun(tree, max_parallel=2)


class _SyncOnlyLeaf(ScalarQuery):
    """A ScalarQuery declared sync-only; folds into HAS_SYNC_ONLY_ATOM."""

    async_affinity = Declared(value=False)

    def _compile(self, nid, children):
        def thunk(rt):
            return 3

        return thunk

    def _acompile(self, nid, children):
        async def athunk(rt):
            return 3

        return athunk


async def test_parallel_async_over_dyn_with_sync_only_inner_raises() -> None:
    # ParallelAsync forces the loop; the inner tree is sync-only. The forced
    # loop-mode + sync_atom_on_loop check surfaces this as an error/warning
    # during dispatch of the inner program. Confirm the invocation blows up.
    tree = ParallelAsync(Eval(ConstCarrier(_SyncOnlyLeaf())))
    with pytest.raises(RuntimeError, match=r"sync-only atom.*on the event loop"):
        await arun(tree, max_parallel=2)


async def test_race_over_dyn_with_sync_only_inner_raises() -> None:
    tree = Race(Eval(ConstCarrier(_SyncOnlyLeaf())))
    with pytest.raises(RuntimeError, match=r"sync-only atom.*on the event loop"):
        await arun(tree, max_parallel=2)


async def test_anyn_over_dyn_with_sync_only_inner_raises() -> None:
    tree = AnyN(Eval(ConstCarrier(_SyncOnlyLeaf())))
    with pytest.raises(RuntimeError, match=r"sync-only atom.*on the event loop"):
        await arun(tree, max_parallel=2)
