"""Slot-role attributes: which slot indices play what role in a node.

Specifically a Control concern. A Control's slot 0 is its parameter (a
*yielding child*: Ref, Query, or Action); the remaining slots are its
body (*mutating children*: Command, Action, or Flow). The declared
``param_slots`` attribute names which slot indices are parameter slots
on each Control kind (e.g. ``If`` and ``While`` declare ``frozenset({0})``).
Other Flow kinds (Strategy) and non-Flow kinds keep the empty default and
have no param slots.

This is structural metadata, like ``sort``, but per-slot. Laws that need
to distinguish body from parameter (``flow_body_is_mutator``,
``control_param_is_yielder``) read this column.
"""

from __future__ import annotations

from nu.engine import Attribute, Declared

from .names import Attr


__all__ = ["ATTRIBUTES"]


ATTRIBUTES: tuple[Attribute, ...] = (Declared(value=frozenset(), name=Attr.PARAM_SLOTS),)
