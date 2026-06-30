"""Effects attribute: what a Nu program touches in the Context.

An effect is an *observable* interaction with the Context, bound to the
*fabric* it acts through: a READ materializes a value, a WRITE transforms it.
Nothing declares an effect. A kind declares ``mutates`` - the slot indices it
writes to - and effects are synthesized by pairing a Ref with how it gets used:
mutation on a Ref is a WRITE, a Ref in any other slot self-yields a READ, and
mutation on a non-Ref is a local change that contributes no effect at all.

The fabric a Ref touches is identified by the Ref's concrete *class*, never a
location name. A location can be static or computed at eval time, so its name
is not knowable from the tree; what *is* knowable is which fabric the Ref binds
into, and each fabric has its own concrete Ref class. So an effect tuple is
``(ref_class, effect)``: two effects conflict when they share a fabric class.

The declared ``mutates`` annotates a sort's mutation slots; the synthesized
``composition_effects`` folds a subtree's whole effect set. Purity is a derived
fact, not an attribute: ``composition_effects`` is empty.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu.engine import Attribute, Declared, Synthesized

from .names import Attr
from .sort import Sort


if TYPE_CHECKING:
    from nu.engine.compilation import Path, Program
    from nu.lang.kinds import Ref

__all__ = ["ATTRIBUTES", "Effect", "EffectSet"]


class Effect(StrEnum):
    """An observable interaction with the Context, carried in an effect tuple."""

    READ = "read"
    WRITE = "write"


type EffectSet = frozenset[tuple[type[Ref], Effect]]


def _tracked_effects(program: Program, path: Path) -> EffectSet:
    """The (ref_class, effect) tuples a node contributes through its Ref children.

    A Ref child in a mutation slot (an index in ``mutates``) binds as a WRITE;
    a Ref child in any other slot binds as a READ. A non-Ref child contributes
    nothing - a mutation with no address is a local change, not an effect, so a
    WRITE annotation over a Literal computes to no tuple at all.

    Each tuple carries the Ref child's concrete *class* - the fabric it touches.
    The location name is never read: it may not exist statically, and conflict
    is decided at fabric granularity, which the class identifies.
    """
    mutates: frozenset[int] = program.attr(path, Attr.MUTATES)
    path_of = program.path_of
    children = [path_of[c] for c in program.children[program.id_of[path]]]
    tuples: set[tuple[type[Ref], Effect]] = set()
    for slot, child in enumerate(children):
        if program.attr(child, Attr.SORT) != Sort.REF:
            continue
        ref_class = type(program.terms[program.id_of[child]])
        tuples.add((ref_class, Effect.WRITE if slot in mutates else Effect.READ))
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
