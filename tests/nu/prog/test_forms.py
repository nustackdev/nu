"""``Program``: the Form over source text, and what its verbs compose to.

Covers both verbs standalone, every construction argument threading through
each of them, the ``on_error`` branch under both runtimes, and what a catch
branch can read off the caught error. The substrate refs that mix this Form
into a stored slot are tested next to their own substrates
(``tests/nu/kv/functional/test_prog_ref.py``, ``tests/nu/mem/test_prog_ref.py``).
"""

from __future__ import annotations

import os
import sys
import textwrap

import pytest

import nu
from nu.prog import ConstructionError, LoadNu, Program, PyBrace


def src(text: str) -> str:
    return textwrap.dedent(text).lstrip()


GREETING = src("""
    import nu

    def out(who='world'):
        return nu.Str('hello ' + who)
""")

BROKEN = src("""
    import nu

    def out():
        return 1 / 0
""")

PID = src("""
    import nu
    import os

    def out():
        return nu.Int(os.getpid())
""")


def venv_brace(body: nu.Nu, tag: object = None) -> nu.Nu:
    if tag is None:
        return nu.Provide(PyBrace, {"python": sys.executable}, body)
    return nu.Provide(PyBrace, {"python": sys.executable}, body, tag=tag)


# --- construction -------------------------------------------------------


def test_a_bare_string_is_all_it_takes() -> None:
    # No ``.of()`` classmethod: TypedNu wraps one child and a plain str
    # literalizes on the way into the tree, so the source is the child.
    assert nu.run(nu.Str(Program(GREETING)))[0] == GREETING


def test_program_is_flat_on_the_nu_surface() -> None:
    assert nu.Program is Program


def test_program_is_hashable() -> None:
    # Nothing here overrides ``__eq__``, so the default identity hash stands
    # and a Program can sit in a set or a dict key like any other Nu.
    assert len({Program(GREETING), Program(GREETING)}) == 2


# --- .load() ------------------------------------------------------------


def test_load_composes_a_loadnu_over_the_source() -> None:
    tree = Program(GREETING).load()
    assert isinstance(tree, LoadNu)
    assert tree._children[0] is not None


def test_load_yields_a_term_without_running_it() -> None:
    term, _ = nu.run(Program(GREETING).load())
    assert isinstance(term, nu.Nu)
    assert nu.run(term)[0] == "hello world"


async def test_load_yields_a_term_async() -> None:
    term, _ = await nu.arun(Program(GREETING).load())
    assert isinstance(term, nu.Nu)


# --- .run() -------------------------------------------------------------


def test_run_composes_eval_over_load() -> None:
    tree = Program(GREETING).run()
    assert isinstance(tree, nu.Eval)
    assert isinstance(tree._children[0], LoadNu)


def test_run_drives_the_constructed_term() -> None:
    assert nu.run(Program(GREETING).run())[0] == "hello world"


async def test_run_drives_the_constructed_term_async() -> None:
    value, _ = await nu.arun(Program(GREETING).run())
    assert value == "hello world"


# --- argument threading, both verbs -------------------------------------


ENTRY_SOURCE = src("""
    import nu

    def build():
        return nu.Str('built')
""")


def test_entry_threads_through_run() -> None:
    assert nu.run(Program(ENTRY_SOURCE).run(entry="build"))[0] == "built"


def test_entry_threads_through_load() -> None:
    term, _ = nu.run(Program(ENTRY_SOURCE).load(entry="build"))
    assert nu.run(term)[0] == "built"


def test_entry_can_be_computed() -> None:
    ctx = nu.Context()
    ctx.attrs["entry"] = "build"
    tree = Program(ENTRY_SOURCE).run(entry=nu.AttrRef("entry"))
    assert nu.run(tree, ctx)[0] == "built"


def test_scope_threads_through_run() -> None:
    assert nu.run(Program(GREETING).run(scope={"who": "you"}))[0] == "hello you"


def test_scope_threads_through_load() -> None:
    term, _ = nu.run(Program(GREETING).load(scope={"who": "you"}))
    assert nu.run(term)[0] == "hello you"


def test_scope_values_can_be_computed() -> None:
    ctx = nu.Context()
    ctx.attrs["who"] = "attrs"
    tree = Program(GREETING).run(scope={"who": nu.AttrRef("who")})
    assert nu.run(tree, ctx)[0] == "hello attrs"


def test_filename_threads_through_run() -> None:
    with pytest.raises(ConstructionError) as excinfo:
        nu.run(Program(BROKEN).run(filename="<movies>"))
    assert "<movies>" in excinfo.value.diagnostic.traceback


def test_filename_threads_through_load() -> None:
    with pytest.raises(ConstructionError) as excinfo:
        nu.run(Program(BROKEN).load(filename="<jobs>"))
    assert "<jobs>" in excinfo.value.diagnostic.traceback


def test_brace_threads_through_run() -> None:
    # Two live braces, one tagged. The tag decides which interpreter built
    # the term, so the two pids differ.
    tree = venv_brace(
        venv_brace(
            nu.Eq(Program(PID).run(brace="second"), Program(PID).run()),
            tag="second",
        )
    )
    assert nu.run(tree)[0] is False


def test_brace_threads_through_load() -> None:
    # Only a tagged brace is bound, so an untagged load falls back in-process
    # and the tagged one goes out to the child. The two pids prove which.
    tagged, _ = nu.run(venv_brace(Program(PID).load(brace="second"), tag="second"))
    untagged, _ = nu.run(venv_brace(Program(PID).load(), tag="second"))
    assert nu.run(tagged)[0] != os.getpid()
    assert nu.run(untagged)[0] == os.getpid()


# --- the subprocess path ------------------------------------------------


def test_run_under_a_venv_brace() -> None:
    assert nu.run(venv_brace(Program(GREETING).run()))[0] == "hello world"


async def test_run_under_a_venv_brace_async() -> None:
    value, _ = await nu.arun(venv_brace(Program(GREETING).run()))
    assert value == "hello world"


def test_a_venv_brace_builds_in_the_child_not_here() -> None:
    child_pid, _ = nu.run(venv_brace(Program(PID).run()))
    assert child_pid != os.getpid()


def test_scope_crosses_into_a_venv_brace() -> None:
    tree = venv_brace(Program(GREETING).run(scope={"who": "venv"}))
    assert nu.run(tree)[0] == "hello venv"


def test_a_venv_brace_failure_still_raises() -> None:
    with pytest.raises(ConstructionError):
        nu.run(venv_brace(Program(BROKEN).run()))


# --- on_error -----------------------------------------------------------


def test_without_on_error_a_construction_failure_propagates() -> None:
    with pytest.raises(ConstructionError):
        nu.run(Program(BROKEN).run())


def test_on_error_wraps_in_a_trycatch() -> None:
    tree = Program(BROKEN).run(on_error=nu.Literal("caught"))
    assert isinstance(tree, nu.TryCatch)
    assert tree._payload["errors"] == (ConstructionError,)


def test_on_error_branch_runs_and_forwards_its_value() -> None:
    assert nu.run(Program(BROKEN).run(on_error=nu.Literal("caught")))[0] == "caught"


async def test_on_error_branch_runs_under_arun() -> None:
    value, _ = await nu.arun(Program(BROKEN).run(on_error=nu.Literal("caught")))
    assert value == "caught"


def test_on_error_leaves_a_working_program_alone() -> None:
    tree = Program(GREETING).run(on_error=nu.Literal("caught"))
    assert nu.run(tree)[0] == "hello world"


def test_on_error_does_not_swallow_what_the_program_itself_raises() -> None:
    # The filter is ConstructionError only. This snippet constructs fine and
    # blows up while running, which is the program's failure, not the load's.
    boom = src("""
        import nu

        def out():
            return nu.Int(1) / nu.Int(0)
    """)
    with pytest.raises(ZeroDivisionError):
        nu.run(Program(boom).run(on_error=nu.Literal("caught")))


def test_on_error_also_catches_a_venv_brace_failure() -> None:
    tree = venv_brace(Program(BROKEN).run(on_error=nu.Literal("caught")))
    assert nu.run(tree)[0] == "caught"


# --- reading the diagnostic from inside the catch branch ----------------


def test_the_catch_branch_can_read_the_error_as_a_string() -> None:
    tree = Program(BROKEN).run(on_error=nu.str(nu.AttrRef("error")))
    value, _ = nu.run(tree)
    assert "ZeroDivisionError" in value
    assert "(line 4)" in value


def test_the_catch_branch_can_read_the_diagnostic_fields() -> None:
    # Two Vars hops: the exception's __dict__ carries ``diagnostic``, the
    # Diagnostic's carries ``lineno``. Both need a __dict__, which is why
    # neither type is slotted.
    exc = nu.GetAttr(nu.AttrRef("error"), "exception")
    diagnostic = nu.GetItem(nu.Vars(exc), "diagnostic")
    lineno = nu.GetItem(nu.Vars(diagnostic), "lineno")
    assert nu.run(Program(BROKEN).run(on_error=lineno))[0] == 4


def test_the_catch_branch_can_branch_on_the_line_number() -> None:
    exc = nu.GetAttr(nu.AttrRef("error"), "exception")
    lineno = nu.GetAttr(nu.GetAttr(exc, "diagnostic"), "lineno")
    tree = Program(BROKEN).run(
        on_error=nu.If(nu.Eq(lineno, 4), nu.Literal("line four"), nu.Literal("elsewhere"))
    )
    assert nu.run(tree)[0] == "line four"


async def test_the_catch_branch_reads_the_diagnostic_under_arun() -> None:
    exc = nu.GetAttr(nu.AttrRef("error"), "exception")
    lineno = nu.GetAttr(nu.GetAttr(exc, "diagnostic"), "lineno")
    value, _ = await nu.arun(Program(BROKEN).run(on_error=lineno))
    assert value == 4
