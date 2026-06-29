"""Pre-compilation effect analysis over Term trees.

A tree walk that reads each node's declared mutation slots and yields the
``(Ref, Effect)`` edges of the subtree -- the same information the v2
effect attribute (``nu2.lang.attributes.effects``) synthesizes at compile
time, but available *before* a Program exists. Rewrites that inject
boundaries (Brackets, Policies) run pre-compile and need exactly this.

Folds on top of the walk: ``is_pure`` / ``reads`` / ``writes`` /
``fabrics`` and the fabric predicates ``touches_fabric`` /
``has_write_on_fabric``.

v1 source: ``src/nu/terms/effects.py`` (+ ``shapes/tree/wrap.py`` predicates).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Effect, Ref


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu2.lang import Nu


__all__ = [
    "fabrics",
    "has_write_on_fabric",
    "is_pure",
    "iter_effects",
    "reads",
    "touches_fabric",
    "writes",
]


def iter_effects(node: Nu) -> Iterator[tuple[Ref, Effect]]:
    """Walk the subtree yielding ``(ref_instance, effect)`` for every Ref child.

    Mirrors the v2 effect synthesis (``nu2.lang.attributes.effects``): a Ref
    child in a mutation slot (declared via ``mutates``) binds as WRITE; any
    other Ref child binds as READ. Pre-compilation tree walk -- no Program
    needed.
    """
    mutates_obj = type(node).attributes.get("mutates")
    mutated_slots: frozenset[int] = getattr(mutates_obj, "value", frozenset())
    for slot, child in enumerate(node.children):
        if isinstance(child, Ref):
            yield child, Effect.WRITE if slot in mutated_slots else Effect.READ
    for child in node.children:
        yield from iter_effects(child)


def is_pure(node: Nu) -> bool:
    """An atom or composition with no tracked effects is pure."""
    return next(iter_effects(node), None) is None


def reads(node: Nu) -> frozenset[Ref]:
    """Refs the subtree reads."""
    return frozenset(ref for ref, eff in iter_effects(node) if eff is Effect.READ)


def writes(node: Nu) -> frozenset[Ref]:
    """Refs the subtree writes."""
    return frozenset(ref for ref, eff in iter_effects(node) if eff is Effect.WRITE)


def fabrics(node: Nu) -> frozenset[type]:
    """Fold the subtree's Refs to the set of fabric identities they touch.

    Stub, as in v1: a Ref's fabric identity is its type. The real fabric
    model (a Ref carrying its bound fabric) lands with the fabric phase;
    callers that group by fabric should go through this so the swap is
    one place.
    """
    return frozenset(type(ref) for ref, _ in iter_effects(node))


def touches_fabric(node: Nu, ref_types: tuple[type, ...]) -> bool:
    """Predicate: subtree holds at least one Ref whose type is in ref_types."""
    return any(isinstance(ref, ref_types) for ref, _ in iter_effects(node))


def has_write_on_fabric(node: Nu, ref_types: tuple[type, ...]) -> bool:
    """Predicate: subtree has a WRITE effect through a Ref of given type."""
    return any(
        eff is Effect.WRITE and isinstance(ref, ref_types) for ref, eff in iter_effects(node)
    )
