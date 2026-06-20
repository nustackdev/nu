"""Tests for the dynamic atoms (Python's runtime evaluation builtins).

Evaluable atoms (Eval, Compile) are driven over literal-string operands to
check they fold operand values into the real builtin. Structural atoms
(Globals, Locals, Exec) are checked at the attribute level only - they read or
write the live namespace fabric, which is not wired yet, so they are not
evaluated.
"""

from __future__ import annotations

import asyncio
import builtins
import types

from nu2.core.dynamic import Compile, Eval, Exec, Globals, Locals
from nu2.core.literal import Literal
from nu2.lang import EMPTY, INVALID, Attr, Effect, Ref, compile
from nu2.lang.helpers import aeval, eval


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


def test_exec_declares_a_namespace_write():
    program = compile(Exec(Ref("ns"), Literal("x = 1")))
    effects = program.attr(program.root, Attr.COMPOSITION_EFFECTS)
    assert ("ns", Effect.WRITE) in effects
