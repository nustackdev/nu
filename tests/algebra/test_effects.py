"""Tests for effect tracking - static analysis of fabric interactions.

Covers all three computation rules plus edge cases:
1. Literal -> empty
2. Ref -> READ + recurse children
3. Op -> overrides + recurse, union all
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu import Context, Literal, Nu
from nu.terms.effect import Direction, TrackedEffect, is_pure, tracked_effects
from nu.terms.op import BinaryOp, UnaryOp
from nu.terms.ref import Ref


READ = Direction.READ
WRITE = Direction.WRITE


# ---------------------------------------------------------------------------
# Test fixtures - minimal concrete types
# ---------------------------------------------------------------------------


class FabricA(Ref[int]):
    """Test ref for fabric A."""

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def resolve(self, ctx: Context) -> str:
        return "a"

    async def fetch(self, ctx: Context) -> int:
        return 0


class FabricB(Ref[int]):
    """Test ref for fabric B."""

    def __init__(self) -> None:
        super().__init__()

    async def resolve(self, ctx: Context) -> str:
        return "b"

    async def fetch(self, ctx: Context) -> int:
        return 0


class StoreOp(BinaryOp[None]):
    overrides: ClassVar[dict[int, Direction]] = {0: WRITE}

    def apply(self, ref_val: Any, value: Any) -> None:
        return None


class LoadOp(UnaryOp[object]):
    overrides: ClassVar[dict[int, Direction]] = {0: READ}

    def apply(self, value: Any) -> object:
        return value


class AddOp(BinaryOp[int]):
    def apply(self, left: Any, right: Any) -> int:
        return left + right


# ---------------------------------------------------------------------------
# Rule 1: Literal -> empty
# ---------------------------------------------------------------------------


def test_literal_no_effects():
    assert tracked_effects(Literal(42)) == frozenset()


def test_literal_is_pure():
    assert is_pure(Literal(42)) is True


# ---------------------------------------------------------------------------
# Rule 2: Ref -> READ
# ---------------------------------------------------------------------------


def test_ref_produces_read():
    ref = FabricA()
    effects = tracked_effects(ref)
    assert effects == frozenset({TrackedEffect(FabricA, READ)})


def test_ref_is_not_pure():
    ref = FabricA()
    assert is_pure(ref) is False


def test_ref_with_child_ref_dynamic_address():
    """Ref with a child Ref (dynamic address) -> both READs."""
    inner = FabricB()
    outer = FabricA(inner)
    effects = tracked_effects(outer)
    assert TrackedEffect(FabricA, READ) in effects
    assert TrackedEffect(FabricB, READ) in effects
    assert len(effects) == 2


# ---------------------------------------------------------------------------
# Rule 3: Op with overrides
# ---------------------------------------------------------------------------


def test_store_op_write():
    """StoreOp(ref, literal) -> WRITE only."""
    ref = FabricA()
    tree = StoreOp(ref, Literal(42))
    effects = tracked_effects(tree)
    assert effects == frozenset({TrackedEffect(FabricA, WRITE)})


def test_load_op_read():
    """LoadOp(ref) -> READ only."""
    ref = FabricA()
    tree = LoadOp(ref)
    effects = tracked_effects(tree)
    assert effects == frozenset({TrackedEffect(FabricA, READ)})


def test_store_load_increment():
    """StoreOp(ref, AddOp(LoadOp(ref), Literal(1))) -> READ + WRITE."""
    ref = FabricA()
    tree = StoreOp(ref, AddOp(LoadOp(ref), Literal(1)))
    effects = tracked_effects(tree)
    assert TrackedEffect(FabricA, WRITE) in effects
    assert TrackedEffect(FabricA, READ) in effects
    assert len(effects) == 2


# ---------------------------------------------------------------------------
# Pure ops
# ---------------------------------------------------------------------------


def test_add_literals_pure():
    """AddOp(Literal(1), Literal(2)) -> empty (pure)."""
    tree = AddOp(Literal(1), Literal(2))
    assert tracked_effects(tree) == frozenset()
    assert is_pure(tree) is True


def test_add_refs_read():
    """AddOp(ref_a, ref_b) -> READ from both fabrics."""
    ref_a = FabricA()
    ref_b = FabricB()
    tree = AddOp(ref_a, ref_b)
    effects = tracked_effects(tree)
    assert TrackedEffect(FabricA, READ) in effects
    assert TrackedEffect(FabricB, READ) in effects
    assert is_pure(tree) is False


def test_add_same_ref_type():
    """AddOp(ref_a, ref_a2) -> single READ (same fabric type, deduped)."""
    ref_a1 = FabricA()
    ref_a2 = FabricA()
    tree = AddOp(ref_a1, ref_a2)
    effects = tracked_effects(tree)
    assert effects == frozenset({TrackedEffect(FabricA, READ)})


# ---------------------------------------------------------------------------
# Bare Nu (Seq via |)
# ---------------------------------------------------------------------------


def test_bare_nu_seq_mixed():
    """Bare Nu with mixed children unions effects."""
    ref = FabricA()
    tree = Literal(1) | StoreOp(ref, Literal(2)) | LoadOp(ref)
    effects = tracked_effects(tree)
    assert TrackedEffect(FabricA, WRITE) in effects
    assert TrackedEffect(FabricA, READ) in effects


def test_bare_nu_pure_children():
    """Bare Nu with only literals is pure."""
    tree = Literal(1) | Literal(2) | Literal(3)
    assert is_pure(tree) is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_is_pure_empty_nu():
    """Empty bare Nu has no effects."""
    tree = Nu()
    assert is_pure(tree) is True


def test_store_with_dynamic_ref_address():
    """StoreOp where the ref has a child ref (dynamic address).

    Override applies WRITE to the outer ref, but the child ref
    still contributes READ.
    """
    inner_ref = FabricB()
    outer_ref = FabricA(inner_ref)
    tree = StoreOp(outer_ref, Literal(99))
    effects = tracked_effects(tree)
    assert TrackedEffect(FabricA, WRITE) in effects
    assert TrackedEffect(FabricB, READ) in effects
    assert len(effects) == 2


def test_deeply_nested_effects():
    """Effects propagate through deep nesting."""
    ref = FabricA()
    # add(add(add(ref, lit), lit), lit) - ref buried 3 levels deep
    tree = AddOp(AddOp(AddOp(ref, Literal(1)), Literal(2)), Literal(3))
    effects = tracked_effects(tree)
    assert effects == frozenset({TrackedEffect(FabricA, READ)})


def test_tracked_effect_equality():
    """TrackedEffect is a frozen dataclass - equality by value."""
    e1 = TrackedEffect(FabricA, READ)
    e2 = TrackedEffect(FabricA, READ)
    assert e1 == e2
    assert hash(e1) == hash(e2)


def test_tracked_effect_different_direction():
    e_read = TrackedEffect(FabricA, READ)
    e_write = TrackedEffect(FabricA, WRITE)
    assert e_read != e_write


def test_tracked_effect_different_fabric():
    e_a = TrackedEffect(FabricA, READ)
    e_b = TrackedEffect(FabricB, READ)
    assert e_a != e_b
