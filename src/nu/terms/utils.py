"""Tree analysis helpers.

    tracked_effects(nu)  - compute the set of TrackedEffects in a tree.
    is_pure(nu)          - True iff tracked_effects(nu) is empty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .ref import Ref
from .types import Direction, TrackedEffect


if TYPE_CHECKING:
    from .nu import Nu


__all__ = [
    "is_pure",
    "tracked_effects",
]


def _as_positions(spec: int | tuple[int, ...]) -> frozenset[int]:
    if isinstance(spec, int):
        return frozenset({spec})
    return frozenset(spec)


def _position_map(op: object) -> dict[int, Direction]:
    result: dict[int, Direction] = {}
    for i in _as_positions(op.reads):  # type: ignore[attr-defined]
        result[i] = Direction.READ
    for i in _as_positions(op.writes):  # type: ignore[attr-defined]
        result[i] = Direction.WRITE
    return result


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Compute the set of tracked effects for a Nu tree.

    Rules:
        1. Literal -> no effects
        2. Ref (not at a declared position) -> {(type(ref), READ)} + children
        3. Interaction with reads/writes -> check declared positions, recurse
    """
    from .interaction import Interaction
    from .query import Literal

    if isinstance(nu, Literal):
        return frozenset()

    if isinstance(nu, Interaction):
        effects: set[TrackedEffect] = set()
        positions = _position_map(nu)
        for i, child in enumerate(nu.children):
            if i in positions and isinstance(child, Ref):
                effects.add(TrackedEffect(type(child), positions[i]))
                for grandchild in child.children:
                    effects |= tracked_effects(grandchild)
            else:
                effects |= tracked_effects(child)
        return frozenset(effects)

    if isinstance(nu, Ref):
        effects = {TrackedEffect(type(nu), Direction.READ)}
        for child in nu.children:
            effects |= tracked_effects(child)
        return frozenset(effects)

    # Bare Nu (plain composition, NuIndepComm): recurse, union.
    result: set[TrackedEffect] = set()
    for child in nu.children:
        result |= tracked_effects(child)
    return frozenset(result)


def is_pure(nu: Nu) -> bool:
    """True if the Nu tree has no tracked effects."""
    return len(tracked_effects(nu)) == 0
