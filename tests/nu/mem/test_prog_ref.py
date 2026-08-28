"""Functional tests for ``ProgramRef`` on the dict substrate.

A stored program is source text in a slot plus the ``Program`` verbs on the
ref, so these drive the whole loop through a dict-backed context: write
source into a slot, read it back, then run what it constructs. The Form's own
surface is covered in ``tests/nu/prog/test_forms``.

The MRO pin at the bottom is the one test here that guards a silent failure
rather than a loud one.
"""

from __future__ import annotations

import sys
import textwrap

import pytest

import nu
from nu import Context, Shape, arun, run
from nu.lang import Sort
from nu.lang.forms import TypedNu
from nu.mem import ProgramRef
from nu.mem.refs.base import RefBase
from nu.prog import ConstructionError, PyBrace


def src(text: str) -> str:
    return textwrap.dedent(text).lstrip()


ADDER = src("""
    import nu

    def out(left=1, right=2):
        return nu.Add(left, right)
""")

BROKEN = src("""
    import nu

    def out():
        return 1 / 0
""")

OTHER = src("""
    import nu

    def out():
        return nu.Str('other')
""")


class App(Shape):
    job = ProgramRef.slot()


@pytest.fixture
def app_ctx() -> Context:
    """Context with a fresh root dict scoped to the App shape."""
    return Context().bind(dict, {}, App)


# --- storage round trip -------------------------------------------------


def test_source_stores_and_reads_back_verbatim(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    assert run(App.job, app_ctx)[0] == ADDER


def test_a_stored_program_runs(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    assert run(App.job.run(), app_ctx)[0] == 3


async def test_a_stored_program_runs_async(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    value, _ = await arun(App.job.run(), app_ctx)
    assert value == 3


def test_a_stored_program_loads_without_running(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    term, _ = run(App.job.load(), app_ctx)
    assert isinstance(term, nu.Nu)
    assert run(term)[0] == 3


def test_scope_reaches_a_stored_program(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    assert run(App.job.run(scope={"left": 10, "right": 5}), app_ctx)[0] == 15


def test_replacing_the_source_replaces_the_program(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    assert run(App.job.run(), app_ctx)[0] == 3
    run(App.job.set(OTHER), app_ctx)
    assert run(App.job.run(), app_ctx)[0] == "other"


def test_a_stored_program_runs_in_a_venv_brace(app_ctx: Context) -> None:
    run(App.job.set(ADDER), app_ctx)
    tree = nu.Provide(PyBrace, {"python": sys.executable}, App.job.run())
    assert run(tree, app_ctx)[0] == 3


# --- failures -----------------------------------------------------------


def test_a_broken_stored_program_raises(app_ctx: Context) -> None:
    run(App.job.set(BROKEN), app_ctx)
    with pytest.raises(ConstructionError):
        run(App.job.run(), app_ctx)


def test_on_error_catches_a_broken_stored_program(app_ctx: Context) -> None:
    run(App.job.set(BROKEN), app_ctx)
    assert run(App.job.run(on_error=nu.Literal("caught")), app_ctx)[0] == "caught"


def test_on_error_can_read_the_diagnostic_line(app_ctx: Context) -> None:
    run(App.job.set(BROKEN), app_ctx)
    exc = nu.GetAttr(nu.AttrRef("error"), "exception")
    lineno = nu.GetAttr(nu.GetAttr(exc, "diagnostic"), "lineno")
    assert run(App.job.run(on_error=lineno), app_ctx)[0] == 4


# --- MRO pin ------------------------------------------------------------


def test_the_substrate_base_wins_the_mro() -> None:
    # Bases are ``(ItemRef, Program)``. Flipped, ``TypedNu`` would win both
    # of these: the sort would drop to a scalar query and ``_compile`` would
    # become a passthrough over child 0, which is the parent ref, not the
    # stored value. Neither failure raises, so it is pinned here.
    assert ProgramRef._attributes["sort"].value is Sort.REF
    assert ProgramRef._compile is RefBase._compile
    assert ProgramRef._compile is not TypedNu._compile
