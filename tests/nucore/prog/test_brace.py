"""PyBrace: the brace as a ctx-bound resource.

The transport itself is covered in ``test_constructors.py``. This file is
only about the resource wrapper: which constructor it builds, that setup
and cleanup drive the child, and that both lifecycles work.
"""

from __future__ import annotations

import sys

import nu
from nu.prog.brace import PyBrace
from nu.prog.constructors import InProcess, Venv


HELLO = "import nu\n\ndef out():\n    return nu.Str('hi')\n"


# --- which constructor it wraps -----------------------------------------


def test_no_python_is_the_in_process_brace() -> None:
    assert isinstance(PyBrace().constructor, InProcess)


def test_a_python_path_is_a_venv_brace() -> None:
    assert isinstance(PyBrace(sys.executable).constructor, Venv)


def test_the_constructor_is_built_once() -> None:
    brace = PyBrace()
    assert brace.constructor is brace.constructor


# --- lifecycle ----------------------------------------------------------


def test_setup_starts_the_child_and_cleanup_reaps_it() -> None:
    brace = PyBrace(sys.executable)
    brace.setup(nu.Context())
    proc = brace.constructor._proc
    assert brace.started
    brace.cleanup()
    assert not brace.started
    assert proc.poll() is not None


def test_setup_on_an_in_process_brace_is_trivial() -> None:
    brace = PyBrace()
    brace.setup(nu.Context())
    assert not brace.started  # nothing to start
    brace.cleanup()


def test_cleanup_is_idempotent() -> None:
    brace = PyBrace(sys.executable)
    brace.setup(nu.Context())
    brace.cleanup()
    brace.cleanup()
    assert not brace.started


async def test_async_lifecycle_starts_and_stops_the_child() -> None:
    brace = PyBrace(sys.executable)
    await brace.asetup(nu.Context())
    assert brace.started
    term = await brace.aconstruct(HELLO)
    assert isinstance(term, nu.Nu)
    await brace.acleanup()
    assert not brace.started


# --- it is itself a constructor -----------------------------------------


def test_a_brace_forwards_construct() -> None:
    brace = PyBrace()
    value, _ = nu.run(brace.construct(HELLO))
    assert value == "hi"


def test_construct_starts_a_venv_brace_lazily() -> None:
    brace = PyBrace(sys.executable)
    try:
        assert isinstance(brace.construct(HELLO), nu.Nu)
        assert brace.started
    finally:
        brace.cleanup()
