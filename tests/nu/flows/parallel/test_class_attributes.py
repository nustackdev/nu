"""Declared-attribute basis for the Parallel / Race / AnyN taxonomy.

Pins ``EXEC_ORDER=PARALLEL`` across the whole family and the
``REQUIRES_ASYNC`` split: ``ParallelAsync`` forces the loop up to the whole
subtree (True); ``ParallelThreaded`` and plain ``Parallel`` do not (False).
``Race`` / ``AnyN`` are async-only.
"""

from __future__ import annotations

from nu.context import AttrRef, SetCmd
from nu.core import Literal
from nu.flows import (
    AnyN,
    Parallel,
    ParallelAsync,
    ParallelThreaded,
    Race,
)
from nu.lang import Attr, compile
from nu.lang.attributes.execution import ExecOrder


def _set(name: str, value: object) -> SetCmd:
    return SetCmd(AttrRef(name), Literal(value))


def test_all_kinds_declare_parallel_exec_order() -> None:
    for kind in (
        Parallel,
        ParallelThreaded,
        ParallelAsync,
        Race,
        AnyN,
    ):
        program = compile(kind(_set("a", 1)))
        assert program.attr(program.root, Attr.EXEC_ORDER) is ExecOrder.PARALLEL


def test_parallel_and_parallel_threaded_do_not_require_async() -> None:
    for kind in (Parallel, ParallelThreaded):
        program = compile(kind(_set("a", 1)))
        assert program.attr(program.root, Attr.REQUIRES_ASYNC) is False


def test_parallel_async_requires_async() -> None:
    program = compile(ParallelAsync(_set("a", 1)))
    assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True


def test_race_and_any_require_async() -> None:
    for kind in (Race, AnyN):
        program = compile(kind(_set("a", 1)))
        assert program.attr(program.root, Attr.REQUIRES_ASYNC) is True


def test_force_mode_flags_line_up() -> None:
    assert Parallel._FORCE_MODE is None
    assert ParallelThreaded._FORCE_MODE == "threaded"
    assert ParallelAsync._FORCE_MODE == "async"
