"""Slot-role attributes: which slot indices play what role in a node.

Two declared per-slot columns, both structural metadata like ``sort`` but
per-slot.

``param_slots`` is a Control concern. A Control's slot 0 is its parameter (a
*yielding child*: Ref, Query, or Action); the remaining slots are its
body (*mutating children*: Command, Action, or Flow). ``param_slots`` names
which slot indices are parameter slots on each Control kind (e.g. ``If`` and
``While`` declare ``frozenset({0})``). Other Flow kinds (Strategy) and non-Flow
kinds keep the empty default. Laws that distinguish body from parameter
(``flow_body_is_mutator``, ``control_param_is_yielder``) read this column.

``structural`` names the slot indices a kind fills with address *structure*
rather than a value to evaluate - a hierarchical Ref's parent (``children[0]``),
a reactive subscription's source. A structural slot is never evaluated at run:
the atom resolves it into an address specially. It is orthogonal to ``mutates``
and outside the effect system - because the slot is never evaluated, no READ
arises to suppress. Generic passes (effect walk, load annotation, inline) read
this column to leave those slots unevaluated while still recursing into them.
Most kinds keep the empty default.
"""

from __future__ import annotations

from nu.engine import Attribute, Declared

from .names import Attr


__all__ = ["ATTRIBUTES"]


ATTRIBUTES: tuple[Attribute, ...] = (
    Declared(value=frozenset(), name=Attr.PARAM_SLOTS),
    Declared(value=frozenset(), name=Attr.STRUCTURAL),
)
