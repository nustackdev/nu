"""Effect tracking - static analysis of fabric interactions.

Computes tracked effects by walking a Nu tree. Tree analysis utility,
not stored on nodes.

Two directions:
    READ  - data pulled from fabric into compute space
    WRITE - state changed at fabric location

A TrackedEffect = (fabric Ref class, direction) pair.

Effect declaration on Op subclasses:
    writes: int | tuple[int, ...] = ()
    reads:  int | tuple[int, ...] = ()

Three computation rules:
    1. Literal -> no effects (empty set)
    2. Ref (not at a declared position) -> {(type(ref), READ)} + children
    3. Op -> check writes/reads per child position, recurse, union all
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


def _as_positions(spec: int | tuple[int, ...]) -> frozenset[int]:
    """Normalize `int | tuple[int, ...]` to a frozenset."""
    if isinstance(spec, int):
        return frozenset({spec})
    return frozenset(spec)


def _position_map(op: Op) -> dict[int, Direction]:
    """Build {position: Direction} from an Op's `writes` / `reads` attrs."""
    result: dict[int, Direction] = {}
    for i in _as_positions(op.reads):
        result[i] = Direction.READ
    for i in _as_positions(op.writes):
        # WRITE wins if both are declared (use of READ|WRITE on same pos is unusual)
        result[i] = Direction.WRITE
    return result


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Compute the set of tracked effects for a Nu tree.

    Args:
        nu: Root of the Nu tree to analyze.

    Returns:
        Frozenset of TrackedEffect pairs.
    """
    # Rule 1: Literal -> no effects
    if isinstance(nu, Literal):
        return frozenset()

    # Rule 3: Op -> check declared positions, recurse children
    if isinstance(nu, Op):
        effects: set[TrackedEffect] = set()
        positions = _position_map(nu)
        for i, child in enumerate(nu.children):
            if i in positions and isinstance(child, Ref):
                effects.add(TrackedEffect(type(child), positions[i]))
                # Still recurse into ref's children (dynamic address parts)
                for grandchild in child.children:
                    if isinstance(grandchild, Nu):
                        effects |= tracked_effects(grandchild)
            else:
                effects |= tracked_effects(child)
        return frozenset(effects)

    # Rule 2: Ref (not at declared position - handled above) -> READ + children
    if isinstance(nu, Ref):
        effects = {TrackedEffect(type(nu), Direction.READ)}
        for child in nu.children:
            if isinstance(child, Nu):
                effects |= tracked_effects(child)
        return frozenset(effects)

    # Bare Nu (plain composition, NuIndepComm) or other nodes: recurse, union
    result: set[TrackedEffect] = set()
    for child in nu.children:
        if isinstance(child, Nu):
            result |= tracked_effects(child)
    return frozenset(result)


def is_pure(nu: Nu) -> bool:
    """Return True if the Nu tree has no tracked effects."""
    return len(tracked_effects(nu)) == 0
