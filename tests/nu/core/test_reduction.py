"""Structural tests for the reduction atoms.

Reductions consume a stream child and the stream runtime is not wired yet, so
these stay structural: compile a reduction over a stream source and assert the
node is SCALAR over a STREAM child, and a clean reduction validates against
the law set. No eval.
"""

from __future__ import annotations

import pytest

from nu.core import Iter, Literal
from nu.core.reduction import (
    AllOf,
    AnyOf,
    Collect,
    Count,
    First,
    Last,
    Max,
    Min,
    Sum,
)
from nu.lang import LAWS, Attr, Cardinality, compile, gate, validate


_FOLDS = [
    Sum,
    Min,
    Max,
    AnyOf,
    AllOf,
    Count,
    First,
    Last,
    Collect,
]


def _stream() -> Iter:
    return Iter(Literal(range(10)))


@pytest.mark.parametrize("fold", _FOLDS)
def test_reduction_is_scalar_over_a_stream(fold):
    program = compile(fold(_stream()))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


@pytest.mark.parametrize("fold", _FOLDS)
def test_a_reduction_validates(fold):
    program = compile(fold(_stream()))
    assert validate(program, *LAWS) is program


def test_a_scalar_in_the_stream_slot_is_refused():
    # A reduction over a scalar child violates the cardinality law: a fold
    # needs a stream to consume.
    verdict = gate(compile(Sum(Literal(1))), *LAWS)
    assert any(v.law == "reduction_takes_stream" for v in verdict)


# --- evaluation (Sum, Collect) -------------------------------------------


def test_sum_folds_a_stream_to_its_total():
    from nu.lang.helpers import run

    value, _ = run(Sum(Iter(Literal(range(1, 5)))))
    assert value == 10


def test_collect_drains_a_stream_to_a_list():
    from nu.lang.helpers import run

    value, _ = run(Collect(Iter(Literal(range(3)))))
    assert value == [0, 1, 2]


def test_min_and_max_fold_the_extremes():
    from nu.lang.helpers import run

    assert run(Min(Iter(Literal([3, 1, 2]))))[0] == 1
    assert run(Max(Iter(Literal([3, 1, 2]))))[0] == 3


def test_min_of_an_empty_stream_is_empty():
    from nu.lang import EMPTY
    from nu.lang.helpers import run

    assert run(Min(Iter(Literal([]))))[0] is EMPTY


def test_any_and_all_fold_truthiness():
    from nu.lang.helpers import run

    assert run(AnyOf(Iter(Literal([0, 0, 1]))))[0] is True
    assert run(AnyOf(Iter(Literal([0, 0, 0]))))[0] is False
    assert run(AllOf(Iter(Literal([1, 2, 3]))))[0] is True
    assert run(AllOf(Iter(Literal([1, 0, 3]))))[0] is False


def test_count_counts_items():
    from nu.lang.helpers import run

    assert run(Count(Iter(Literal([1, 2, 3, 4]))))[0] == 4


def test_first_and_last_take_the_ends():
    from nu.lang.helpers import run

    assert run(First(Iter(Literal([10, 20, 30]))))[0] == 10
    assert run(Last(Iter(Literal([10, 20, 30]))))[0] == 30


def test_first_of_an_empty_stream_is_empty():
    from nu.lang import EMPTY
    from nu.lang.helpers import run

    assert run(First(Iter(Literal([]))))[0] is EMPTY
