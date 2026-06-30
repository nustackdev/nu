"""Effects laws: well-formedness of mutation and effect annotations.

A non-yielding mutator (a VOID-cardinality Command) is observable only by
landing a WRITE on Context, so its mutation slot *must* hold a Ref. A yielding
mutator (an Action, scalar or stream) is observable through its yield, so its
mutation slot *need not* hold a Ref - addressless, it just degrades to a Query.
The Ref-slot law therefore fires off cardinality, not off "declares a mutation".
The second
law is a sanity check: every effect a node attributes to its subtree is sourced
from a Ref present somewhere beneath it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr, Cardinality, Sort

from .predicates import attr_true, cardinality_is, child_paths


if TYPE_CHECKING:
    from nu.engine import Path, Program


__all__ = ["LAWS"]


# --- ref-typed slots ----------------------------------------------------


def _unfilled_ref_slot(program: Program, path: Path) -> int | None:
    """The first mutation slot not filled by a Ref, if any."""
    children = child_paths(program, path)
    for slot in program.attr(path, Attr.MUTATES):
        if slot < len(children) and program.attr(children[slot], Attr.SORT) is not Sort.REF:
            return slot
    return None


@predicate
def ref_slots_hold_refs(program: Program, path: Path) -> bool:
    """Holds when every mutation slot of a non-yielding mutator holds a Ref."""
    return _unfilled_ref_slot(program, path) is None


def ref_slot_detail(program: Program, path: Path) -> str:
    """Name the mutation slot that should hold a Ref but does not."""
    return f"slot {_unfilled_ref_slot(program, path)} must hold a Ref"


# --- effects originate at refs ------------------------------------------


def _subtree_ref_classes(program: Program, path: Path) -> set[type]:
    """Every Ref class found in the subtree rooted at ``path``."""
    classes: set[type] = set()
    for descendant in program.walk(path):
        if program.attr(descendant, Attr.SORT) is Sort.REF:
            classes.add(type(program.terms[program.id_of[descendant]]))
    return classes


def _orphan_effect_class(program: Program, path: Path) -> type | None:
    """The first effect-tuple class with no matching Ref in the subtree, if any."""
    classes = _subtree_ref_classes(program, path)
    for ref_class, _ in program.attr(path, Attr.COMPOSITION_EFFECTS):
        if ref_class not in classes:
            return ref_class
    return None


@predicate
def effects_have_ref_source(program: Program, path: Path) -> bool:
    """Holds when every composition-effect tuple is sourced from a subtree Ref."""
    return _orphan_effect_class(program, path) is None


def orphan_effect_detail(program: Program, path: Path) -> str:
    """Name the orphan effect tuple whose Ref source is missing."""
    orphan = _orphan_effect_class(program, path)
    name = orphan.__name__ if orphan is not None else None
    return f"effect on '{name}' has no corresponding Ref in subtree"


# --- laws ---------------------------------------------------------------


LAWS: tuple[Law, ...] = (
    Law(
        "ref_slots",
        scope=cardinality_is(Cardinality.VOID) & attr_true(Attr.MUTATES),
        holds=ref_slots_hold_refs,
        message=ref_slot_detail,
    ),
    Law(
        "effects_originate_at_refs",
        scope=attr_true(Attr.COMPOSITION_EFFECTS),
        holds=effects_have_ref_source,
        message=orphan_effect_detail,
    ),
)
