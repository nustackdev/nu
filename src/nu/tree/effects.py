"""Pre-compilation effect analysis over Term trees.

A tree walk that reads each node's declared mutation slots and yields the
``(Ref, Effect)`` edges of the subtree -- the same information the
effect attribute (``nu.lang.attributes.effects``) synthesizes at compile
time, but available *before* a Program exists. Rewrites that inject
boundaries (Brackets, Policies) run pre-compile and need exactly this.

Folds on top of the walk: ``is_pure`` / ``reads`` / ``writes`` /
``fabrics`` and the fabric predicates ``touches_fabric`` /
``has_write_on_fabric``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Effect, Ref
from nu.lang.attributes import Sort


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang import Nu


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

    Mirrors the effect synthesis (``nu.lang.attributes.effects``): a Ref
    child in a mutation slot (declared via ``mutates``) binds as WRITE; a Ref
    child in a structural slot (declared via ``structural``) binds as nothing -
    it is address structure, never evaluated; any other Ref child binds as
    READ. The recursion still descends every child, so value reads nested
    inside a structural subtree are collected. Pre-compilation tree walk -- no
    Program needed.
    """
    attrs = type(node)._attributes
    mutated_slots: frozenset[int] = getattr(attrs.get("mutates"), "value", frozenset())
    structural_slots: frozenset[int] = getattr(attrs.get("structural"), "value", frozenset())
    for slot, child in enumerate(node._children):
        if isinstance(child, Ref) and slot not in structural_slots:
            yield child, Effect.WRITE if slot in mutated_slots else Effect.READ
    for child in node._children:
        yield from iter_effects(child)


def _is_dynamic(node: Nu) -> bool:
    attrs = getattr(type(node), "_attributes", None)
    if not attrs:
        return False
    sort_attr = attrs.get("sort")
    return getattr(sort_attr, "value", None) is Sort.DYNAMIC


def _has_dyn(node: Nu) -> bool:
    if _is_dynamic(node):
        return True
    return any(_has_dyn(c) for c in node._children)


def is_pure(node: Nu) -> bool:
    """An atom or composition with no tracked effects is pure.

    A subtree carrying a dynamic (Sort.DYNAMIC) node is never pure: the
    inner tree the carrier will produce is opaque at analysis time, so we
    treat the whole subtree as potentially effectful.
    """
    if _has_dyn(node):
        return False
    return next(iter_effects(node), None) is None


def reads(node: Nu) -> frozenset[Ref]:
    """Refs the subtree reads."""
    return frozenset(ref for ref, eff in iter_effects(node) if eff is Effect.READ)


def writes(node: Nu) -> frozenset[Ref]:
    """Refs the subtree writes."""
    return frozenset(ref for ref, eff in iter_effects(node) if eff is Effect.WRITE)


def fabrics(node: Nu) -> frozenset[type]:
    """Fold the subtree's Refs to the set of fabric identities they touch.

    A Ref's fabric identity is its type.
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
