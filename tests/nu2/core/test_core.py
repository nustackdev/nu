"""Functional tests for the Nu core symbols built on nu2.lang.

Compile real core programs and check the attributes the language assigns:
effects, cardinality, sync/async, and the law set.
"""

from __future__ import annotations

from nu2.core import (
    Add,
    Delete,
    Emit,
    Eq,
    If,
    Literal,
    Lt,
    Mul,
    Par,
    Range,
    Seq,
    Set,
    Sum,
    Watch,
    While,
)
from nu2.core.runtime import Context, run
from nu2.lang import LAWS, Attr, Cardinality, Effect, Ref, compile, gate, validate


# --- effects -------------------------------------------------------------


def test_arithmetic_is_pure():
    program = compile(Add(Literal(1), Literal(2)))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset()


def test_set_tracks_a_write_and_a_read():
    program = compile(Set(Ref("total"), Add(Ref("total"), Literal(1))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("total", Effect.WRITE), ("total", Effect.READ)}
    )


def test_a_flow_folds_every_command_effect():
    program = compile(Seq(Set(Ref("a"), Literal(1)), Set(Ref("b"), Literal(2))))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {("a", Effect.WRITE), ("b", Effect.WRITE)}
    )


# --- cardinality ---------------------------------------------------------


def test_reduction_is_scalar_over_a_stream():
    program = compile(Sum(Range(Literal(0), Literal(10))))
    assert program.attr(program.root, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR
    assert program.attr((0,), Attr.CHILD_CARDINALITY) is Cardinality.STREAM


# --- sync / async --------------------------------------------------------


def test_a_watch_puts_the_program_on_a_loop():
    assert compile(Seq(Set(Ref("x"), Literal(1)))).attr((), Attr.ON_LOOP) is False
    assert compile(Emit(Ref("out"), Watch())).attr((), Attr.ON_LOOP) is True


# --- algebra -------------------------------------------------------------


def test_declared_algebra_reaches_the_program():
    program = compile(Add(Literal(1), Literal(2)))
    assert program.attr(program.root, Attr.COMMUTATIVE) is True
    assert program.attr(program.root, Attr.ASSOCIATIVE) is True


# --- laws ----------------------------------------------------------------


def test_a_clean_program_validates():
    program = compile(Seq(Set(Ref("a"), Literal(1)), Set(Ref("b"), Add(Ref("a"), Literal(1)))))
    assert validate(program, *LAWS) is program


def test_a_command_in_a_query_slot_is_refused():
    verdict = gate(compile(Add(Set(Ref("x"), Literal(1)), Literal(2))), *LAWS)
    assert any(v.law == "composition" for v in verdict)


def test_a_parallel_flow_runs_its_commands():
    program = compile(Par(Set(Ref("a"), Literal(1)), Set(Ref("b"), Literal(2))))
    assert program.attr(program.root, Attr.EXEC_ORDER) is not None
    assert validate(program, *LAWS) is program


def test_a_control_holds_commands_under_a_condition():
    program = compile(If(Eq(Ref("flag"), Literal(1)), Set(Ref("done"), Literal(1))))
    assert validate(program, *LAWS) is program


# --- execution -----------------------------------------------------------


def test_a_set_writes_an_evaluated_query():
    ctx = run(compile(Set(Ref("x"), Add(Literal(2), Literal(3)))))
    assert ctx.store == {"x": 5}


def test_a_reduction_runs_over_a_stream_source():
    ctx = run(compile(Set(Ref("n"), Sum(Range(Literal(0), Literal(5))))))
    assert ctx.store == {"n": 10}


def test_a_ref_reads_what_an_earlier_command_wrote():
    program = compile(
        Seq(
            Set(Ref("a"), Literal(10)),
            Set(Ref("b"), Mul(Ref("a"), Literal(3))),
        )
    )
    assert run(program).store == {"a": 10, "b": 30}


def test_an_if_runs_its_body_only_when_the_condition_holds():
    taken = run(compile(If(Lt(Literal(1), Literal(2)), Set(Ref("hit"), Literal(1)))))
    skipped = run(compile(If(Lt(Literal(2), Literal(1)), Set(Ref("hit"), Literal(1)))))
    assert taken.store == {"hit": 1}
    assert skipped.store == {}


def test_a_while_loops_until_the_condition_fails():
    program = compile(
        While(
            Lt(Ref("i"), Literal(4)),
            Set(Ref("i"), Add(Ref("i"), Literal(1))),
        )
    )
    assert run(program, Context(i=0)).store == {"i": 4}


def test_a_delete_drops_a_ref():
    program = compile(Seq(Set(Ref("gone"), Literal(1)), Delete(Ref("gone"))))
    assert run(program).store == {}


def test_an_emit_appends_to_a_stream_ref():
    program = compile(Seq(Emit(Ref("log"), Literal("a")), Emit(Ref("log"), Literal("b"))))
    assert run(program, Context(log=[])).store == {"log": ["a", "b"]}


def test_run_starts_from_a_supplied_context():
    ctx = run(compile(Set(Ref("y"), Add(Ref("y"), Literal(1)))), Context(y=41))
    assert ctx.store == {"y": 42}
