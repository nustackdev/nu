"""Effect tracking - static analysis of fabric interactions.

Computes tracked effects by walking a Nu tree. This is a tree analysis
utility, not stored on nodes.

Two directions:
    READ  - data pulled from fabric into compute space
    WRITE - state changed at fabric location

A TrackedEffect = (fabric Ref class, direction) pair.

Three computation rules:
    1. Literal -> no effects (empty set)
    2. Ref (not at override position) -> {(type(ref), READ)} + children
    3. Op -> check overrides per child position, recurse, union all
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Flag, auto

from .literal import Literal
from .nu import Nu
from .op import Op
from .ref import Ref


__all__ = [
    "Direction",
    "TrackedEffect",
    "is_pure",
    "tracked_effects",
]


class Direction(Flag):
    """Tracked direction of fabric interaction."""

    READ = auto()
    WRITE = auto()


@dataclass(frozen=True)
class TrackedEffect:
    """A single tracked effect: which fabric, which direction."""

    fabric: type
    direction: Direction

    def __repr__(self) -> str:
        return f"TrackedEffect({self.fabric.__name__}, {self.direction.name})"


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Compute the set of tracked effects for a Nu tree.

    Walks the tree applying the three rules:
    1. Literal -> empty set
    2. Ref (not at an override position) -> READ + recurse children
    3. Op -> apply overrides for override positions, recurse rest, union

    Args:
        nu: Root of the Nu tree to analyze.

    Returns:
        Frozenset of TrackedEffect pairs.
    """
    # Rule 1: Literal -> no effects
    if isinstance(nu, Literal):
        return frozenset()

    # Rule 3: Op -> check overrides, recurse children
    if isinstance(nu, Op):
        effects: set[TrackedEffect] = set()
        overrides = getattr(nu, "overrides", {})
        for i, child in enumerate(nu.children):
            if i in overrides and isinstance(child, Ref):
                # Override position: use declared direction instead of default READ
                effects.add(TrackedEffect(type(child), overrides[i]))
                # Still recurse into ref's children (dynamic address parts)
                for grandchild in child.children:
                    if isinstance(grandchild, Nu):
                        effects |= tracked_effects(grandchild)
            else:
                effects |= tracked_effects(child)
        return frozenset(effects)

    # Rule 2: Ref (not at override position - handled above) -> READ + children
    if isinstance(nu, Ref):
        effects = {TrackedEffect(type(nu), Direction.READ)}
        for child in nu.children:
            if isinstance(child, Nu):
                effects |= tracked_effects(child)
        return frozenset(effects)

    # Bare Nu (Seq via |) or other nodes: recurse children, union
    result: set[TrackedEffect] = set()
    for child in nu.children:
        if isinstance(child, Nu):
            result |= tracked_effects(child)
    return frozenset(result)


def is_pure(nu: Nu) -> bool:
    """Return True if the Nu tree has no tracked effects."""
    return len(tracked_effects(nu)) == 0
