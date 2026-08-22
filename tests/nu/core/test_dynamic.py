"""Tests for the dynamic atoms (Python's runtime evaluation builtins).

Evaluable atoms (Eval, Compile) are driven over literal-string operands to
check they fold operand values into the real builtin. The escape-hatch atoms
(Globals, Locals, Exec) reach the host namespace directly; they are checked at
the attribute level and driven to confirm they bypass the Context into raw
Python.
"""

from __future__ import annotations

import asyncio
import builtins
import types

from nu.core.dynamic import Compile as Compile
from nu.core.dynamic import Eval as Eval
from nu.core.dynamic import Exec as Exec
from nu.core.dynamic import Globals as Globals
from nu.core.dynamic import Locals as Locals
from nu.core.literal import Literal
from nu.lang import EMPTY, INVALID, Attr, Effect, Ref
from nu.lang.helpers import aeval, compile, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- evaluable: Eval / Compile -------------------------------------------


def test_eval_evaluates_an_expression():
    assert _eval(Eval(Literal("1+1"))) == 2
    assert _eval(Eval(Literal("[x for x in range(3)]"))) == [0, 1, 2]


def test_eval_with_explicit_namespaces():
    # globals / locals passed as operand dicts, not a live Context.
    assert _eval(Eval(Literal("a + b"), Literal({}), Literal({"a": 2, "b": 3}))) == 5


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(Eval(Literal("2*3")))) == 6


def test_eval_propagates_a_sentinel():
    assert _eval(Eval(Literal(EMPTY))) is INVALID
    assert _eval(Eval(Literal("a"), Literal(INVALID))) is INVALID


def test_compile_yields_a_code_object():
    code = _eval(Compile(Literal("1+1"), Literal("<test>"), Literal("eval")))
    assert isinstance(code, types.CodeType)
    # The produced code object is a real, runnable Python code object.
    assert builtins.eval(code) == 2  # noqa: S307


def test_compile_propagates_a_sentinel():
    assert _eval(Compile(Literal(INVALID), Literal("<t>"), Literal("eval"))) is INVALID


# --- structural: Globals / Locals / Exec ---------------------------------


def test_globals_and_locals_are_scalar_queries():
    # Pure attribute check: structural, no live-namespace fabric needed here.
    assert compile(Globals()).attr((), Attr.COMPOSITION_EFFECTS) == frozenset()
    assert compile(Locals()).attr((), Attr.COMPOSITION_EFFECTS) == frozenset()


def test_exec_has_no_mutates_but_still_mutates_dict():
    # Exec is a ScalarQuery (no mutates declared) - slot 0 is a plain dict,
    # not a Ref, so no fabric write is declared. It still mutates the passed-in
    # dict and returns it (escape-hatch semantics: host-visible only).
    program = compile(Exec(Ref(), Literal("x = 1")))
    effects = program.attr(program.root, Attr.COMPOSITION_EFFECTS)
    assert (Ref, Effect.WRITE) not in effects
    # Actual mutation verified via evaluation in test_exec_runs_statements_into_a_namespace_dict.


# --- escape-hatch evaluation ---------------------------------------------


def test_globals_returns_the_host_namespace_dict():
    assert isinstance(_eval(Globals()), dict)


def test_locals_returns_a_dict():
    assert isinstance(_eval(Locals()), dict)


def test_exec_runs_statements_into_a_namespace_dict():
    ns = _eval(Exec(Literal({}), Literal("x = 21 * 2")))
    assert ns["x"] == 42


def test_exec_propagates_a_sentinel():
    assert _eval(Exec(Literal(INVALID), Literal("x = 1"))) is INVALID
