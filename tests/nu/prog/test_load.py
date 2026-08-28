"""LoadNu: python source in, a Nu term out.

Covers the term LoadNu yields, the ``Eval(LoadNu(...))`` pair under both
runtimes, brace resolution (bound, tagged, and the unbound fallback),
Nu-computed source and scope children, and the failure surface.
"""

from __future__ import annotations

import os
import sys
import textwrap

import pytest

import nu
from nu.prog import ConstructionError, LoadNu, PyBrace


def src(text: str) -> str:
    return textwrap.dedent(text).lstrip()


# A snippet an expression could not be: it defines a class at module level
# and the entry point builds a tree over it.
GREETING = src("""
    import nu

    class Greeting:
        def __init__(self, who):
            self.who = who

        def render(self):
            return 'hello ' + self.who

    def out(who='world'):
        return nu.Str(Greeting(who).render())
""")

HELLO = src("""
    import nu

    def out():
        return nu.Str('hi')
""")

BROKEN = src("""
    import nu

    def out():
        return 1 / 0
""")

# Which interpreter built the term, reported as a Nu the parent can run.
PID = src("""
    import nu
    import os

    def out():
        return nu.Int(os.getpid())
""")


def venv_brace(body: nu.Nu, **kwargs: object) -> nu.Nu:
    return nu.Provide(PyBrace, {"python": sys.executable, **kwargs}, body)


# --- LoadNu yields a term -----------------------------------------------


def test_load_yields_a_nu_term() -> None:
    term, _ = nu.run(LoadNu(HELLO))
    assert isinstance(term, nu.Nu)


def test_the_term_it_yields_actually_runs() -> None:
    term, _ = nu.run(LoadNu(HELLO))
    assert nu.run(term)[0] == "hi"


async def test_load_yields_a_nu_term_async() -> None:
    term, _ = await nu.arun(LoadNu(HELLO))
    assert isinstance(term, nu.Nu)
    assert nu.run(term)[0] == "hi"


def test_load_is_flat_on_the_nu_surface() -> None:
    assert nu.LoadNu is LoadNu


# --- Eval(LoadNu(...)) end to end ---------------------------------------


def test_eval_over_load_sync() -> None:
    value, _ = nu.run(nu.Eval(LoadNu(GREETING)))
    assert value == "hello world"


async def test_eval_over_load_async() -> None:
    value, _ = await nu.arun(nu.Eval(LoadNu(GREETING)))
    assert value == "hello world"


# --- brace resolution ---------------------------------------------------


def test_no_brace_bound_falls_back_to_in_process() -> None:
    # A bare LoadNu in a plain tree, no Provide anywhere.
    value, _ = nu.run(nu.Eval(LoadNu(GREETING)))
    assert value == "hello world"


def test_in_process_brace_bound_by_provide() -> None:
    tree = nu.Provide(PyBrace, {}, nu.Eval(LoadNu(GREETING)))
    assert nu.run(tree)[0] == "hello world"


def test_venv_brace_bound_by_provide() -> None:
    assert nu.run(venv_brace(nu.Eval(LoadNu(GREETING))))[0] == "hello world"


async def test_venv_brace_bound_by_provide_async() -> None:
    value, _ = await nu.arun(venv_brace(nu.Eval(LoadNu(GREETING))))
    assert value == "hello world"


def test_a_venv_brace_builds_in_the_child_not_here() -> None:
    # The proof the brace was used at all: the constructed term carries the
    # pid of whoever built it, and that is not this process.
    child_pid, _ = nu.run(venv_brace(nu.Eval(LoadNu(PID))))
    assert child_pid != os.getpid()
    assert nu.run(nu.Eval(LoadNu(PID)))[0] == os.getpid()


def test_a_tagged_brace_is_selected_by_tag() -> None:
    # Two live children under two brackets. The tag decides which one built
    # the term, so the two pids differ.
    tree = nu.Provide(
        PyBrace,
        {"python": sys.executable},
        nu.Provide(
            PyBrace,
            {"python": sys.executable},
            nu.Eq(
                nu.Eval(LoadNu(PID, brace="second")),
                nu.Eval(LoadNu(PID)),
            ),
            tag="second",
        ),
    )
    assert nu.run(tree)[0] is False


def test_one_child_serves_many_loads_inside_one_provide() -> None:
    tree = venv_brace(
        nu.And(
            nu.Eq(nu.Eval(LoadNu(PID)), nu.Eval(LoadNu(PID))),
            nu.Eq(nu.Eval(LoadNu(PID)), nu.Eval(LoadNu(PID))),
        )
    )
    assert nu.run(tree)[0] is True


# --- computed children --------------------------------------------------


def test_source_can_arrive_from_a_computed_child() -> None:
    # The kv-ref path in miniature: the source is not a literal in the tree,
    # it is read at runtime from somewhere else.
    ctx = nu.Context()
    ctx.attrs["stored_program"] = GREETING
    value, _ = nu.run(nu.Eval(LoadNu(nu.AttrRef("stored_program"))), ctx)
    assert value == "hello world"


def test_scope_values_can_be_computed_children() -> None:
    ctx = nu.Context()
    ctx.attrs["who"] = "kv"
    tree = nu.Eval(LoadNu(GREETING, scope={"who": nu.AttrRef("who")}))
    assert nu.run(tree, ctx)[0] == "hello kv"


async def test_scope_values_can_be_computed_children_async() -> None:
    ctx = nu.Context()
    ctx.attrs["who"] = "kv"
    tree = nu.Eval(LoadNu(GREETING, scope={"who": nu.AttrRef("who")}))
    value, _ = await nu.arun(tree, ctx)
    assert value == "hello kv"


def test_scope_values_cross_into_a_venv_brace() -> None:
    ctx = nu.Context()
    ctx.attrs["who"] = "venv"
    tree = venv_brace(nu.Eval(LoadNu(GREETING, scope={"who": nu.AttrRef("who")})))
    assert nu.run(tree, ctx)[0] == "hello venv"


def test_a_literal_scope_value_auto_wraps() -> None:
    assert nu.run(nu.Eval(LoadNu(GREETING, scope={"who": "you"})))[0] == "hello you"


def test_entry_point_name_is_a_child() -> None:
    source = src("""
        import nu

        def build():
            return nu.Str('built')
    """)
    ctx = nu.Context()
    ctx.attrs["entry"] = "build"
    tree = nu.Eval(LoadNu(source, entry=nu.AttrRef("entry")))
    assert nu.run(tree, ctx)[0] == "built"


def test_filename_is_a_child_and_reaches_the_diagnostic() -> None:
    with pytest.raises(ConstructionError) as excinfo:
        nu.run(LoadNu(BROKEN, filename="<movies>"))
    assert "<movies>" in excinfo.value.diagnostic.traceback


# --- failures -----------------------------------------------------------


def test_a_failing_snippet_raises_with_a_usable_diagnostic() -> None:
    with pytest.raises(ConstructionError) as excinfo:
        nu.run(LoadNu(BROKEN))
    diag = excinfo.value.diagnostic
    assert diag.lineno == 4
    assert "ZeroDivisionError" in diag.message
    assert "1 / 0" in diag.traceback


async def test_a_failing_snippet_raises_under_arun() -> None:
    with pytest.raises(ConstructionError):
        await nu.arun(LoadNu(BROKEN))


def test_a_failing_snippet_in_a_venv_brace_raises_too() -> None:
    with pytest.raises(ConstructionError) as excinfo:
        nu.run(venv_brace(LoadNu(BROKEN)))
    assert "ZeroDivisionError" in excinfo.value.diagnostic.message


def test_a_syntax_error_raises() -> None:
    with pytest.raises(ConstructionError, match="does not parse"):
        nu.run(LoadNu("def out(:\n    pass\n"))


def test_load_never_yields_a_diagnostic() -> None:
    # The whole reason it raises: a downstream Eval only ever sees terms.
    with pytest.raises(ConstructionError):
        nu.run(nu.Eval(LoadNu(BROKEN)))


# --- Eval's placement law, as it lands on a loaded tree -----------------
#
# Recorded, not endorsed. Eval checks the *inner* tree's atoms against where
# the Eval node itself sits, so a loaded program can be refused for reasons
# that live entirely in the outer tree. Neither branch is anything LoadNu or
# Provide(PyBrace, ...) introduces: a plain Literal carrier does the same,
# and a brace bracket is portable, so it never puts the root on the loop.


def test_a_brace_bracket_does_not_put_the_tree_on_the_loop() -> None:
    from nu.lang.attributes import Attr

    tree = venv_brace(nu.Eval(LoadNu(HELLO)))
    program = nu.compile(tree)
    assert program.attrs[Attr.HAS_ASYNC_ONLY_ATOM][0] is False
    assert program.attrs[Attr.ON_LOOP][0] is False


async def test_an_async_only_loaded_tree_is_refused_off_the_loop() -> None:
    source = src("""
        import nu

        def out():
            return nu.Race(nu.Literal(1), nu.Literal(2))
    """)
    with pytest.raises(RuntimeError, match="placed off the event loop"):
        await nu.arun(nu.Eval(LoadNu(source)))


async def test_a_sync_only_loaded_tree_is_refused_on_the_loop() -> None:
    # Timeout is async-only, so it puts the whole tree on the loop, and the
    # loaded tree's sync-only atom is then out of place.
    source = src("""
        import nu

        def out():
            return nu.std.time.sleep(0.0)
    """)
    with pytest.raises(RuntimeError, match="placed on the event loop"):
        await nu.arun(nu.Timeout(5.0, nu.Eval(LoadNu(source))))


# --- slow tier: the whole pipeline over a genuinely foreign venv --------


@pytest.mark.slow
def test_the_pipeline_runs_a_program_authored_against_a_foreign_dep(tmp_path) -> None:
    # test_constructors covers the transport against a foreign venv; this
    # covers the same venv reached through Provide(PyBrace) + Eval(LoadNu).
    from .test_constructors import build_foreign_venv

    root = build_foreign_venv(tmp_path / "foreign")
    source = src("""
        import nu
        import six

        class Tagged:
            tag = six.text_type('dune')

        def out():
            return nu.Str(Tagged.tag)
    """)
    tree = nu.Provide(PyBrace, {"python": str(root)}, nu.Eval(LoadNu(source)))
    assert nu.run(tree)[0] == "dune"
