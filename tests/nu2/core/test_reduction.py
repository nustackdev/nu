"""Structural tests for the reduction atoms.

Reductions consume a stream child and the stream runtime is not wired yet, so
these stay structural: compile a reduction over a stream source and assert the
node is SCALAR over a STREAM child, its declared algebra reaches the program,
and a clean reduction validates against the law set. No eval.
"""

from __future__ import annotations

import pytest

from nu2.core import Iter, Literal
from nu2.core.reduction import All, Any, Collect, Count, First, Last, Max, Min, Sum
from nu2.lang import LAWS, Attr, Cardinality, compile, gate, validate


# All nine atoms, with the algebra each declares.
_FOLDS = [Sum, Min, Max, Any, All, Count, First, Last, Collect]
_COMMUTATIVE = {Sum, Min, Max, Any, All, Count}
_IDEMPOTENT = {Min, Max, Any, All}


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
    for fold in (First, Last, Collect):
        program = compile(fold(_stream()))
        assert program.attr(program.root, Attr.COMMUTATIVE) is False


def test_a_scalar_in_the_stream_slot_is_refused():
    # A reduction over a scalar child violates the cardinality law: a fold
    # needs a stream to consume.
    verdict = gate(compile(Sum(Literal(1))), *LAWS)
    assert any(v.law == "reduction_takes_stream" for v in verdict)


# --- evaluation (Sum, Collect) -------------------------------------------


def test_sum_folds_a_stream_to_its_total():
    from nu2.lang.helpers import run

    value, _ = run(Sum(Iter(Literal(range(1, 5)))))
    assert value == 10


def test_collect_drains_a_stream_to_a_list():
    from nu2.lang.helpers import run

    value, _ = run(Collect(Iter(Literal(range(3)))))
    assert value == [0, 1, 2]
