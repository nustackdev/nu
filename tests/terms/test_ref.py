"""Tests for Ref - typed pointer to a location.

New-core shape: `Ref[T]` (Generic), `support` set, `eval`/`aeval`
overrides on the concrete subclass. Ref's `own_effects` is empty by
class-time validator.
"""

from __future__ import annotations

from typing import ClassVar

from nu import Context, runtime
from nu.terms.nu import NuBase
from nu.terms.ref import Ref
from nu.terms.types import Mode, Realization


# ---------------------------------------------------------------------------
# Minimal concrete Ref for testing the abstract surface
# ---------------------------------------------------------------------------


class StubRef(Ref[int]):
    """Minimal Ref that resolves to a fixed value, sync+async."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, value: int) -> None:
        super().__init__()
        self._value = value

    def eval(self, ctx: Context) -> int:
        return self._value

    async def aeval(self, ctx: Context) -> int:
        return self._value


# ---------------------------------------------------------------------------
# Surface
# ---------------------------------------------------------------------------


def test_ref_is_nu_base():
    assert isinstance(StubRef(42), NuBase)


def test_ref_is_ref():
    assert isinstance(StubRef(42), Ref)


def test_ref_realization_is_scalar():
    assert StubRef(42).realization is Realization.SCALAR


def test_ref_own_effects_empty():
    assert StubRef.own_effects == {}


def test_ref_no_children():
    assert StubRef(42)._children == ()


def test_eval_returns_value(ctx):
    ref = StubRef(42)
    assert ref.eval(ctx) == 42


async def test_aeval_returns_value(ctx):
    ref = StubRef(42)
    assert await ref.aeval(ctx) == 42


# ---------------------------------------------------------------------------
# Drive via runtime (no instance shims on NuBase)
# ---------------------------------------------------------------------------


def test_ref_first_via_runtime(ctx):
    ref = StubRef(7)
    assert runtime.first(ref, ctx) == 7


async def test_ref_afirst_via_runtime(ctx):
    ref = StubRef(7)
    assert await runtime.afirst(ref, ctx) == 7
