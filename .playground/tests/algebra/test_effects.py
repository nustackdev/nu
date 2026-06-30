"""Tests for effect tracking - static analysis over the new core.

`tracked_effects(nu)` returns a `frozenset[(Ref instance, Effect)]`.

Two annotation sources: class-time (`own_effects` on the kind) and
construction-time (Ref bound into a Query slot adds `(ref, READ)`).
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu import Context
from nu.terms.command import ScalarCommand
from nu.terms.effects import is_pure, tracked_effects
from nu.queries.literal import Literal
from nu.terms.query import ScalarQuery
from nu.terms.ref import Ref
from nu.terms.types import Effect, Mode


# ---------------------------------------------------------------------------
# Test fixtures - minimal concrete kinds on the new core
# ---------------------------------------------------------------------------


class FabricA(Ref[int]):
    """Ref on fabric A."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def eval(self, ctx: Context) -> int:
        return 0

    async def aeval(self, ctx: Context) -> int:
        return 0


class FabricB(Ref[int]):
    """Ref on fabric B."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def eval(self, ctx: Context) -> int:
        return 0

    async def aeval(self, ctx: Context) -> int:
        return 0


class StoreCmd(ScalarCommand):
    """Cmd that writes to a Ref at slot 0."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def run(self, ctx: Context) -> None:
        return None

    async def arun(self, ctx: Context) -> None:
        return None


class Add(ScalarQuery):
    """Pure binary add. Operand-driven; effects derived from children."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True
    deterministic: ClassVar[bool] = True

    def _apply(self, ctx: Context, ops: list[Any]) -> int:
        return ops[0] + ops[1]


# ---------------------------------------------------------------------------
# Rule 1: Literal -> empty
# ---------------------------------------------------------------------------


def test_literal_no_effects():
    assert tracked_effects(Literal(42)) == frozenset()


def test_literal_is_pure():
    assert is_pure(Literal(42)) is True


# ---------------------------------------------------------------------------
# Rule 2: Ref alone -> no own effects (Ref's own_effects empty)
# ---------------------------------------------------------------------------


def test_ref_alone_has_no_own_effects():
    """A bare Ref is not a parent edge - no construction-time READ fires."""
    ref = FabricA()
    assert tracked_effects(ref) == frozenset()


# ---------------------------------------------------------------------------
# Rule 3: construction-time READ when Ref binds into a Query slot
# ---------------------------------------------------------------------------


def test_ref_in_query_slot_emits_read():
    """`Add(ref, lit)` - Ref bound into a Query slot adds `(ref, READ)`."""
    ref = FabricA()
    tree = Add(ref, Literal(1))
    effects = tracked_effects(tree)
    assert (ref, Effect.READ) in effects


def test_two_refs_in_query_slots_each_emit_read():
    ra = FabricA()
    rb = FabricB()
    tree = Add(ra, rb)
    effects = tracked_effects(tree)
    assert (ra, Effect.READ) in effects
    assert (rb, Effect.READ) in effects


# ---------------------------------------------------------------------------
# Rule 4: class-time WRITE on a Ref-only slot
# ---------------------------------------------------------------------------


def test_command_write_slot_emits_write():
    """`StoreCmd(ref)` - class-time WRITE on slot 0."""
    ref = FabricA()
    cmd = StoreCmd(ref)
    effects = tracked_effects(cmd)
    assert (ref, Effect.WRITE) in effects
    # Slot 0 is keyed in own_effects; it must NOT also fire construction-time
    # READ - the slot trichotomy makes them disjoint.
    assert (ref, Effect.READ) not in effects


# ---------------------------------------------------------------------------
# Pure ops
# ---------------------------------------------------------------------------


def test_add_literals_pure():
    tree = Add(Literal(1), Literal(2))
    assert tracked_effects(tree) == frozenset()
    assert is_pure(tree) is True


def test_add_refs_not_pure():
    tree = Add(FabricA(), FabricB())
    assert is_pure(tree) is False


# ---------------------------------------------------------------------------
# Subtree propagation
# ---------------------------------------------------------------------------


def test_deeply_nested_effects():
    """Effects propagate through deep nesting."""
    ref = FabricA()
    tree = Add(Add(Add(ref, Literal(1)), Literal(2)), Literal(3))
    effects = tracked_effects(tree)
    assert (ref, Effect.READ) in effects
