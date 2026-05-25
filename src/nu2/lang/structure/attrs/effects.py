"""Effects attribute: what a Nu program touches in the Context.

An effect is one interaction with the Context (RESOLVE, READ or WRITE) bound to
a named location. The declared ``own_effects`` annotates a sort's effect slots;
the synthesized ``composition_effects`` folds a subtree's whole effect set.
Purity is a derived fact, not an attribute: ``composition_effects`` is empty.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute, Declared, Synthesized
from nu2.lang.structure.attrs.names import Attr
from nu2.lang.structure.attrs.sort import Sort


if TYPE_CHECKING:
    from nu2.engine.compilation import Path, Program

__all__ = ["ATTRIBUTES", "Effect", "EffectSet"]


class Effect(StrEnum):
    """An interaction with the Context, carried in a tracked-effect tuple."""

    RESOLVE = "resolve"
    READ = "read"
    WRITE = "write"


type EffectSet = frozenset[tuple[str, Effect]]


def _own_effects(program: Program, path: Path) -> EffectSet:
    """The (ref, effect) tuples a node contributes through its own Ref children.

    A slot the sort annotates contributes that effect; every other slot holding
    a Ref binds in read role. A slot annotated but unfilled contributes nothing.
    """
    annotated: dict[int, Effect] = program.attr(path, Attr.OWN_EFFECTS)
    path_of = program.path_of
    children = [path_of[c] for c in program.children[program.id_of[path]]]
    tuples: set[tuple[str, Effect]] = set()
    for slot, child in enumerate(children):
        if program.attr(child, Attr.SORT) != Sort.REF:
            continue
        name: str = program.terms[program.id_of[child]].payload["name"]
        tuples.add((name, annotated.get(slot, Effect.READ)))
    return frozenset(tuples)


def _union_effects(own: EffectSet, children: list[EffectSet]) -> EffectSet:
    """Fold a subtree's effects: a node's own, plus every child's."""
    return own.union(*children)


ATTRIBUTES: tuple[Attribute, ...] = (
    Declared(value={}, name=Attr.OWN_EFFECTS),
    Synthesized(
        name=Attr.COMPOSITION_EFFECTS,
        base=_own_effects,
        combine=_union_effects,
        reads=(Attr.OWN_EFFECTS, Attr.SORT),
    ),
)
