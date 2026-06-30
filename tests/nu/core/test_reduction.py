"""Structural tests for the reduction atoms.

Reductions consume a stream child and the stream runtime is not wired yet, so
these stay structural: compile a reduction over a stream source and assert the
node is SCALAR over a STREAM child, its declared algebra reaches the program,
and a clean reduction validates against the law set. No eval.
"""

from __future__ import annotations

import pytest

from nu.core import IterQuery, LiteralQuery
from nu.core.reduction import (
    AllQuery,
    AnyQuery,
    CollectQuery,
    CountQuery,
    FirstQuery,
    LastQuery,
    MaxQuery,
    MinQuery,
    SumQuery,
)
from nu.lang import LAWS, Attr, Cardinality, compile, gate, validate


# AllQuery nine atoms, with the algebra each declares.
_FOLDS = [
    SumQuery,
    MinQuery,
    MaxQuery,
    AnyQuery,
    AllQuery,
    CountQuery,
    FirstQuery,
    LastQuery,
    CollectQuery,
]
_COMMUTATIVE = {SumQuery, MinQuery, MaxQuery, AnyQuery, AllQuery, CountQuery}
_IDEMPOTENT = {MinQuery, MaxQuery, AnyQuery, AllQuery}


def _stream() -> IterQuery:
    return IterQuery(LiteralQuery(range(10)))


@pytest.mark.parametrize("fold", _FOLDS)
def test_reduction_is_scalar_over_a_stream(fold):
    program = compile(fold(_stream()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


@pytest.mark.parametrize("fold", _FOLDS)
def test_a_reduction_validates(fold):
    program = compile(fold(_stream()))
    assert validate(program, *LAWS) is program


@pytest.mark.parametrize("fold", sorted(_COMMUTATIVE, key=lambda f: f.__name__))
def test_commutative_associative_folds_reach_the_program(fold):
    program = compile(fold(_stream()))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True


@pytest.mark.parametrize("fold", sorted(_IDEMPOTENT, key=lambda f: f.__name__))
def test_idempotent_folds_reach_the_program(fold):
    program = compile(fold(_stream()))
    assert program.attr(program.root, Attr.IDEMPOTENT) is True


def test_first_last_collect_are_not_commutative():
    # Order-sensitive folds keep the declared default (not commutative).
    for fold in (FirstQuery, LastQuery, CollectQuery):
        program = compile(fold(_stream()))
        assert program.attr(program.root, Attr.COMMUTATIVE) is False


def test_a_scalar_in_the_stream_slot_is_refused():
    # A reduction over a scalar child violates the cardinality law: a fold
    # needs a stream to consume.
    verdict = gate(compile(SumQuery(LiteralQuery(1))), *LAWS)
    assert any(v.law == "reduction_takes_stream" for v in verdict)


# --- evaluation (SumQuery, CollectQuery) -------------------------------------------


def test_sum_folds_a_stream_to_its_total():
    from nu.lang.helpers import run

    value, _ = run(SumQuery(IterQuery(LiteralQuery(range(1, 5)))))
    assert value == 10


def test_collect_drains_a_stream_to_a_list():
    from nu.lang.helpers import run

    value, _ = run(CollectQuery(IterQuery(LiteralQuery(range(3)))))
    assert value == [0, 1, 2]


def test_min_and_max_fold_the_extremes():
    from nu.lang.helpers import run

    assert run(MinQuery(IterQuery(LiteralQuery([3, 1, 2]))))[0] == 1
    assert run(MaxQuery(IterQuery(LiteralQuery([3, 1, 2]))))[0] == 3


def test_min_of_an_empty_stream_is_empty():
    from nu.lang import EMPTY
    from nu.lang.helpers import run

    assert run(MinQuery(IterQuery(LiteralQuery([]))))[0] is EMPTY


def test_any_and_all_fold_truthiness():
    from nu.lang.helpers import run

    assert run(AnyQuery(IterQuery(LiteralQuery([0, 0, 1]))))[0] is True
    assert run(AnyQuery(IterQuery(LiteralQuery([0, 0, 0]))))[0] is False
    assert run(AllQuery(IterQuery(LiteralQuery([1, 2, 3]))))[0] is True
    assert run(AllQuery(IterQuery(LiteralQuery([1, 0, 3]))))[0] is False


def test_count_counts_items():
    from nu.lang.helpers import run

    assert run(CountQuery(IterQuery(LiteralQuery([1, 2, 3, 4]))))[0] == 4


def test_first_and_last_take_the_ends():
    from nu.lang.helpers import run

    assert run(FirstQuery(IterQuery(LiteralQuery([10, 20, 30]))))[0] == 10
    assert run(LastQuery(IterQuery(LiteralQuery([10, 20, 30]))))[0] == 30


def test_first_of_an_empty_stream_is_empty():
    from nu.lang import EMPTY
    from nu.lang.helpers import run

    assert run(FirstQuery(IterQuery(LiteralQuery([]))))[0] is EMPTY
