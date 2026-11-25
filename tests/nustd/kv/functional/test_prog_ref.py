"""Functional tests for ``ProgramRef`` on the virtuals substrate.

A stored program is source text in a leaf plus the ``Program`` verbs on the
ref, so these drive the whole loop through a real virtuals transaction (the
``ctx`` fixture): write source into a slot, read it back, then run what it
constructs. The Form's own surface is covered in ``tests/nu/prog/test_forms``.

The MRO pin at the bottom is the one test here that guards a silent failure
rather than a loud one.
"""

from __future__ import annotations

import sys
import textwrap

import pytest

import nu
from nu import Shape, arun, run
from nu.lang import Form, Sort
from nu.prog import ConstructionError, PyBrace
from nustd.kv import ProgramRef
from nustd.kv.refs.base import PrimitiveRef


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


# --- storage round trip -------------------------------------------------


def test_source_stores_and_reads_back_verbatim(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    assert run(App.job, ctx)[0] == ADDER


def test_a_stored_program_runs(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    assert run(App.job.run(), ctx)[0] == 3


async def test_a_stored_program_runs_async(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    value, _ = await arun(App.job.run(), ctx)
    assert value == 3


def test_a_stored_program_loads_without_running(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    term, _ = run(App.job.load(), ctx)
    assert isinstance(term, nu.Nu)
    assert run(term)[0] == 3


def test_scope_reaches_a_stored_program(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    assert run(App.job.run(scope={"left": 10, "right": 5}), ctx)[0] == 15


def test_replacing_the_source_replaces_the_program(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    assert run(App.job.run(), ctx)[0] == 3
    run(App.job.set(OTHER), ctx)
    assert run(App.job.run(), ctx)[0] == "other"


def test_a_stored_program_runs_in_a_venv_brace(ctx) -> None:
    run(App.job.set(ADDER), ctx)
    tree = nu.Provide(PyBrace, {"python": sys.executable}, App.job.run())
    assert run(tree, ctx)[0] == 3


# --- failures -----------------------------------------------------------


def test_a_broken_stored_program_raises(ctx) -> None:
    run(App.job.set(BROKEN), ctx)
    with pytest.raises(ConstructionError):
        run(App.job.run(), ctx)


def test_on_error_catches_a_broken_stored_program(ctx) -> None:
    run(App.job.set(BROKEN), ctx)
    assert run(App.job.run(on_error=nu.Literal("caught")), ctx)[0] == "caught"


# --- MRO pin ------------------------------------------------------------


def test_the_ref_carries_the_program_surface_not_the_form() -> None:
    # The ref mixes in the Program surface only, never the Form node, so it
    # stays a fabric read: no passthrough over child 0 to shadow.
    assert not issubclass(ProgramRef, Form)
    assert ProgramRef._attributes["sort"].value is Sort.REF
    assert ProgramRef._compile is PrimitiveRef._compile
