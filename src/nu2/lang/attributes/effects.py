"""Effects attribute: what a Nu program touches in the Context.

An effect is an *observable* interaction with the Context, bound to the named
location it acts through: a READ materializes a value, a WRITE transforms it.
Nothing declares an effect. A kind declares ``mutates`` - the slot indices it
writes to - and effects are synthesized by pairing a Ref with how it gets used:
mutation on a Ref is a WRITE, a Ref in any other slot self-yields a READ, and
mutation on a non-Ref is a local change that contributes no effect at all.

The declared ``mutates`` annotates a sort's mutation slots; the synthesized
``composition_effects`` folds a subtree's whole effect set. Purity is a derived
fact, not an attribute: ``composition_effects`` is empty.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu2.engine import Attribute, Declared, Synthesized

from .names import Attr
from .sort import Sort


if TYPE_CHECKING:
    from nu2.engine.compilation import Path, Program

__all__ = ["ATTRIBUTES", "Effect", "EffectSet"]


class Effect(StrEnum):
    """An observable interaction with the Context, carried in an effect tuple."""

    READ = "read"
    WRITE = "write"


type EffectSet = frozenset[tuple[str, Effect]]


def _tracked_effects(program: Program, path: Path) -> EffectSet:
    """The (ref, effect) tuples a node contributes through its own Ref children.

    A Ref child in a mutation slot (an index in ``mutates``) binds as a WRITE;
    a Ref child in any other slot binds as a READ. A non-Ref child contributes
    nothing - a mutation with no address is a local change, not an effect, so a
    WRITE annotation over a Literal computes to no tuple at all.
    """
    mutates: frozenset[int] = program.attr(path, Attr.MUTATES)
    path_of = program.path_of
    children = [path_of[c] for c in program.children[program.id_of[path]]]
    tuples: set[tuple[str, Effect]] = set()
    for slot, child in enumerate(children):
        if program.attr(child, Attr.SORT) != Sort.REF:
            continue
        name: str = program.terms[program.id_of[child]].payload["name"]
        tuples.add((name, Effect.WRITE if slot in mutates else Effect.READ))
    return frozenset(tuples)


def _union_effects(own: EffectSet, children: list[EffectSet]) -> EffectSet:
    """Fold a subtree's effects: a node's own, plus every child's."""
    return own.union(*children)


ATTRIBUTES: tuple[Attribute, ...] = (
    Declared(value=frozenset(), name=Attr.MUTATES),
    Synthesized(
        name=Attr.COMPOSITION_EFFECTS,
        base=_tracked_effects,
        combine=_union_effects,
        reads=(Attr.MUTATES, Attr.SORT),
    ),
)
