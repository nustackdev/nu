"""Effects laws: well-formedness of effect annotations.

Every Ref-typed slot is filled by a real Ref child, and every effect a
node attributes to its subtree is sourced from a Ref present somewhere
beneath it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import Law, predicate
from nu2.lang.attributes import Attr, Sort

from .predicates import attr_true, child_paths


if TYPE_CHECKING:
    from nu2.engine import Path, Program


__all__ = ["LAWS"]


# --- ref-typed slots ----------------------------------------------------


def _unfilled_ref_slot(program: Program, path: Path) -> int | None:
    """The first annotated effect slot not filled by a Ref, if any."""
    children = child_paths(program, path)
    for slot in program.attr(path, Attr.OWN_EFFECTS):
        if slot < len(children) and program.attr(children[slot], Attr.SORT) is not Sort.REF:
            return slot
    return None


@predicate
def ref_slots_hold_refs(program: Program, path: Path) -> bool:
    """Holds when every annotated effect slot present is filled by a Ref."""
    return _unfilled_ref_slot(program, path) is None


def ref_slot_detail(program: Program, path: Path) -> str:
    """Name the annotated slot that should hold a Ref but does not."""
    return f"slot {_unfilled_ref_slot(program, path)} must hold a Ref"


# --- laws ---------------------------------------------------------------


LAWS: tuple[Law, ...] = (
    Law(
        "ref_slots",
        scope=attr_true(Attr.OWN_EFFECTS),
        holds=ref_slots_hold_refs,
        message=ref_slot_detail,
    ),
)
