"""Basic effects example - tracked effect analysis on Nu trees.

Shows the effect system: build trees, then analyze their fabric interactions
without executing anything. Pure static analysis.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu import BinaryOp, Context, Literal, UnaryOp
from nu.terms.effect import Direction, is_pure, tracked_effects
from nu.terms.nu import Nu
from nu.terms.ref import Ref


READ = Direction.READ
WRITE = Direction.WRITE


# ---------------------------------------------------------------------------
# A simple in-memory fabric Ref
# ---------------------------------------------------------------------------


class MemRef(Ref[object]):
    """In-memory fabric ref backed by a shared dict."""

    _store: ClassVar[dict[str, object]] = {}

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key

    async def resolve(self, ctx: Context) -> str:
        return self._key

    async def fetch(self, ctx: Context) -> object:
        return self._store.get(self._key)

    def __repr__(self) -> str:
        return f"MemRef({self._key!r})"


# ---------------------------------------------------------------------------
# Ops with effect overrides
# ---------------------------------------------------------------------------


class StoreOp(BinaryOp[None]):
    """Store a value at a ref location. Position 0 = WRITE target."""

    overrides: ClassVar[dict[int, Direction]] = {0: WRITE}

    def apply(self, ref_val: Any, value: Any) -> None:
        pass  # actual store would happen in execute


class LoadOp(UnaryOp[object]):
    """Load a value from a ref location. Position 0 = READ source."""

    overrides: ClassVar[dict[int, Direction]] = {0: READ}

    def apply(self, value: Any) -> object:
        return value


class AddOp(BinaryOp[float]):
    """Pure addition. No overrides - default rules apply."""

    def apply(self, left: Any, right: Any) -> float:
        return left + right


# ---------------------------------------------------------------------------
# Build trees and analyze effects
# ---------------------------------------------------------------------------


def show(label: str, tree: Nu) -> None:
    """Print effects and purity for a tree."""
    effects = tracked_effects(tree)
    pure = is_pure(tree)
    print(f"\n{label}")
    print(f"  tree:    {tree}")
    print(f"  effects: {sorted(effects, key=lambda e: e.direction.name)}")
    print(f"  pure:    {pure}")


def main() -> None:
    ref = MemRef("x")

    # 1. store(ref, literal) -> WRITE only
    tree1 = StoreOp(ref, Literal(42))
    show("store(ref, 42)", tree1)

    # 2. load(ref) -> READ only
    tree2 = LoadOp(ref)
    show("load(ref)", tree2)

    # 3. store(ref, add(load(ref), literal)) -> READ + WRITE (increment)
    tree3 = StoreOp(ref, AddOp(LoadOp(ref), Literal(1)))
    show("store(ref, add(load(ref), 1))", tree3)

    # 4. add(literal, literal) -> no effects (pure)
    tree4 = AddOp(Literal(3), Literal(4))
    show("add(3, 4)", tree4)

    # 5. add(ref, ref) -> READ (refs materialize)
    ref_a = MemRef("a")
    ref_b = MemRef("b")
    tree5 = AddOp(ref_a, ref_b)
    show("add(ref_a, ref_b)", tree5)

    tree6 = AddOp(MemRef("a"), StoreOp(MemRef("b"), 12))
    show("complex", tree6)

    # Summary
    print("\n--- Summary ---")
    print(f"store(ref, 42)         pure={is_pure(tree1)}")
    print(f"load(ref)              pure={is_pure(tree2)}")
    print(f"store+load (incr)      pure={is_pure(tree3)}")
    print(f"add(3, 4)              pure={is_pure(tree4)}")
    print(f"add(ref_a, ref_b)      pure={is_pure(tree5)}")


if __name__ == "__main__":
    main()
