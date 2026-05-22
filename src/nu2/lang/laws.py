"""Nu's laws: the validity rules an attributed Nu program must satisfy.

Each law is a declarative ``Law``: a ``scope`` selecting the nodes it judges
and a ``holds`` predicate that must be true on each, both drawn from
``predicates``. ``LAWS`` is the full set: feed it to ``gate`` for a verdict or
``validate`` for a rejection.
"""

from __future__ import annotations

from nu2.engine.attribution import Law, Severity
from nu2.lang.attrs import Attr
from nu2.lang.cardinality import Cardinality
from nu2.lang.effects import Effect
from nu2.lang.predicates import (
    attr_true,
    cardinality_is,
    compose_detail,
    composes,
    declares_effect,
    has_children,
    no_child_yields,
    no_composition_effect,
    of_sort,
    ref_slot_detail,
    ref_slots_hold_refs,
)
from nu2.lang.sort import Sort


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = (
    Law(
        "composition",
        scope=has_children,
        holds=composes,
        message=compose_detail,
    ),
    Law(
        "query_no_write",
        scope=of_sort(Sort.QUERY),
        holds=no_composition_effect(Effect.WRITE),
        message="a Query subtree contains a WRITE",
    ),
    Law(
        "command_has_write",
        scope=of_sort(Sort.COMMAND),
        holds=declares_effect(Effect.WRITE),
        message="a Command annotates no WRITE slot",
    ),
    Law(
        "flow_has_command",
        scope=of_sort(Sort.FLOW),
        holds=attr_true(Attr.HAS_COMMAND),
        message="a Flow subtree contains no Command",
    ),
    Law(
        "scalar_stream_refused",
        scope=cardinality_is(Cardinality.SCALAR) & ~of_sort(Sort.REDUCTION),
        holds=no_child_yields(Cardinality.STREAM),
        message="a scalar consumer is fed a stream",
    ),
    Law(
        "ref_slots",
        scope=attr_true(Attr.OWN_EFFECTS),
        holds=ref_slots_hold_refs,
        message=ref_slot_detail,
    ),
    Law(
        "async_atom_needs_loop",
        scope=attr_true(Attr.REQUIRES_ASYNC),
        holds=attr_true(Attr.ON_LOOP),
        message="an async-only atom is resolved off the loop",
    ),
    Law(
        "sync_atom_on_loop",
        scope=~attr_true(Attr.ASYNC_AFFINITY),
        holds=~attr_true(Attr.ON_LOOP),
        message="a sync-only atom is resolved onto the loop",
        severity=Severity.WARNING,
    ),
)
