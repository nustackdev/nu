"""Effects laws: well-formedness of mutation and effect annotations.

A non-yielding mutator (a VOID-cardinality Command) is observable only by
landing a WRITE on Context, so its mutation slot *must* hold a Ref. A yielding
mutator (a SCALAR Action) is observable through its yield, so its mutation slot
*need not* hold a Ref - addressless, it just degrades to a Query. The Ref-slot
law therefore fires off cardinality, not off "declares a mutation". The second
law is a sanity check: every effect a node attributes to its subtree is sourced
from a Ref present somewhere beneath it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import Law, predicate
from nu2.lang.attributes import Attr, Cardinality, Sort

from .predicates import attr_true, cardinality_is, child_paths


if TYPE_CHECKING:
    from nu2.engine import Path, Program


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


def _subtree_ref_names(program: Program, path: Path) -> set[str]:
    """Every Ref payload name found in the subtree rooted at ``path``."""
    names: set[str] = set()
    for descendant in program.walk(path):
        if program.attr(descendant, Attr.SORT) is Sort.REF:
            nid = program.id_of[descendant]
            names.add(program.terms[nid].payload["name"])
    return names


def _orphan_effect_name(program: Program, path: Path) -> str | None:
    """The first effect-tuple name with no matching Ref in the subtree, if any."""
    names = _subtree_ref_names(program, path)
    for name, _ in program.attr(path, Attr.COMPOSITION_EFFECTS):
        if name not in names:
            return name
    return None


@predicate
def effects_have_ref_source(program: Program, path: Path) -> bool:
    """Holds when every composition-effect tuple is sourced from a subtree Ref."""
    return _orphan_effect_name(program, path) is None


def orphan_effect_detail(program: Program, path: Path) -> str:
    """Name the orphan effect tuple whose Ref source is missing."""
    return f"effect on '{_orphan_effect_name(program, path)}' has no corresponding Ref in subtree"


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
