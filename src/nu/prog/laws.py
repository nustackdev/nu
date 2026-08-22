"""Eval placement laws: the one static rule Eval adds.

Eval is a universal child in the composition matrix; the promise + runtime
dispatch handle the interior. The one static rule we keep is on the *carrier*:
the sole child of an Eval must resolve (through Span transparency) to a scalar
yielder, so the runtime always gets exactly one Nu term per evaluation.

This law reads ``child_cardinality`` on the direct child, which the compile
sweep already Span-resolves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr, Cardinality, Sort
from nu.lang.laws.predicates import of_sort


if TYPE_CHECKING:
    from nu.engine import Path, Program


__all__ = ["LAWS"]


@predicate
def _carrier_is_scalar(program: Program, path: Path) -> bool:
    """Holds when Eval's sole child resolves to a SCALAR (through Span)."""
    nid = program.id_of[path]
    child_nids = program.children[nid]
    if not child_nids:
        # Constructor forbids a childless Eval; guard defensively for
        # partially-built programs (phase-isolated tests).
        return False
    child_path = program.path_of[child_nids[0]]
    return program.attr(child_path, Attr.CHILD_CARDINALITY) is Cardinality.SCALAR


LAWS: tuple[Law, ...] = (
    Law(
        "eval_carrier_is_scalar",
        scope=of_sort(Sort.DYNAMIC),
        holds=_carrier_is_scalar,
        message="an Eval's carrier must yield a scalar Nu term (through Span)",
    ),
)
