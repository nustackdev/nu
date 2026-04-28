"""Tree analysis helpers.

tracked_effects(nu)  - compute the set of TrackedEffects in a tree.
is_pure(nu)          - True iff tracked_effects(nu) is empty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._compat_ref import Ref
from ._compat_types import Direction, TrackedEffect


if TYPE_CHECKING:
    from ._compat_nu import Nu


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
    # Phase E: prefer the new `own_effects` declaration. Fall back to legacy
    # `reads` / `writes` tuples when `own_effects` is absent (legacy classes
    # not yet swept).
    own = getattr(op, "own_effects", None)
    if own:
        for i, eff in own.items():
            effs = eff if isinstance(eff, (set, frozenset)) else {eff}
            # New Effect enum values: RESOLVE, READ, WRITE.
            for e in effs:
                name = getattr(e, "name", str(e))
                if name == "WRITE":
                    result[i] = Direction.WRITE
                elif name in ("READ", "RESOLVE"):
                    # Don't override an existing WRITE.
                    result.setdefault(i, Direction.READ)
        return result
    reads = getattr(op, "reads", ())
    writes = getattr(op, "writes", ())
    for i in _as_positions(reads):
        result[i] = Direction.READ
    for i in _as_positions(writes):
        result[i] = Direction.WRITE
    return result


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Compute the set of tracked effects for a Nu tree.

    Rules:
        1. Literal -> no effects
        2. Ref (not at a declared position) -> {(type(ref), READ)} + children
        3. Interaction with reads/writes -> check declared positions, recurse
    """
    from ._compat_interaction import Interaction
    from ._compat_query import Literal

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
