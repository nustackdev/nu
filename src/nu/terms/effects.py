"""Effect machinery - pure traversal over the Nu protocol.

Two annotation sources combine (see
projects/nu/model/04-laws/00-effects-algebra.md):

1. **Class-time** - slot keyed in `own_effects`. Emit `(children[i], eff)`
   for each declared `(slot_idx, effect)`. The kind has already validated
   (composition-time) that `children[i]` is a Ref.
2. **Composition-time** - slot NOT in `own_effects`, NOT a body slot. If
   `children[i]` is a Ref, emit `(children[i], READ)`. The dual-role
   rule.

The slot trichotomy makes the two sources mutually exclusive at the slot
level - no double-annotation guard needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import Effect


if TYPE_CHECKING:
    from collections.abc import Iterable

    from .protocol import Nu
    from .ref import Ref


__all__ = [
    "TrackedEffect",
    "fabrics",
    "is_pure",
    "own_tracked_effects",
    "reads",
    "tracked_effects",
    "writes",
]


# A tracked effect is a (Ref instance, Effect) tuple. The instance, not
# the class - fabric identity may depend on the instance.
TrackedEffect = tuple["Ref", Effect]


def _body_slot_indices(nu: Nu) -> frozenset[int]:
    """Body slot indices for this kind.

    Strategy with `body_slots = ()` means "all child slots are body"
    (its children are Commands per composition matrix).
    """
    cls = type(nu)
    body_slots = getattr(cls, "body_slots", None)
    if body_slots is not None:
        if body_slots == ():
            return frozenset(range(len(nu._children)))
        return frozenset(body_slots)
    body_slot = getattr(cls, "body_slot", None)
    if body_slot is not None:
        return frozenset({body_slot})
    return frozenset()


def _as_set(eff: Effect | frozenset[Effect]) -> frozenset[Effect]:
    if isinstance(eff, Effect):
        return frozenset({eff})
    return eff


def own_tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Effects this atom owns at its own edges. Not recursive."""
    from .ref import Ref

    result: set[TrackedEffect] = set()
    own = type(nu).own_effects
    body = _body_slot_indices(nu)

    for slot_idx, eff in own.items():
        ref = nu._children[slot_idx]
        for e in _as_set(eff):
            result.add((ref, e))  # type: ignore[arg-type]

    for slot_idx, child in enumerate(nu._children):
        if slot_idx in own:
            continue
        if slot_idx in body:
            continue
        if isinstance(child, Ref):
            result.add((child, Effect.READ))

    return frozenset(result)


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Subtree tracked effects: own union recursive over children."""
    result = set(own_tracked_effects(nu))
    for child in nu._children:
        result |= tracked_effects(child)
    return frozenset(result)


def is_pure(nu: Nu) -> bool:
    """An atom or composition with no tracked effects is pure."""
    return len(tracked_effects(nu)) == 0


def fabrics(effs: Iterable[TrackedEffect]) -> frozenset[type]:
    """Fold (Ref, Effect) tuples to the set of fabric identities.

    Stub: Phase A returns `type(ref)` per Ref. The real fabric model
    will refine this in a later phase.
    """
    return frozenset(type(ref) for ref, _ in effs)


def reads(nu: Nu) -> frozenset[Ref]:
    """Refs the subtree reads (RESOLVE + READ)."""
    return frozenset(
        ref for ref, eff in tracked_effects(nu) if eff in (Effect.RESOLVE, Effect.READ)
    )


def writes(nu: Nu) -> frozenset[Ref]:
    """Refs the subtree writes."""
    return frozenset(ref for ref, eff in tracked_effects(nu) if eff is Effect.WRITE)
