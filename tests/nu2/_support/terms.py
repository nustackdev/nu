"""Tiny canonical ``Term`` subclasses for unit tests.

These shapes exercise the engine's structural machinery (TermMeta attribute
collection, Schema resolution, child wiring) without dragging in the Nu
layer-1 surface. Keep them small; if a test needs a Term with a specific
attribute combination not covered here, build it inline in the test --
hoist into this module only when a second test reaches for the same shape.
"""

from __future__ import annotations

from nu2.engine.structure import Declared, Term


__all__ = ["HeavyNode", "Leaf", "Node"]


class Leaf(Term):
    """Childless Term with a single declared ``sort``."""

    sort = Declared(value="Leaf")


class Node(Term):
    """Two-attribute Term that accepts children. Used for child wiring and
    for attribute-override tests via :class:`HeavyNode`."""

    sort = Declared(value="Node")
    weight = Declared(value=1)


class HeavyNode(Node):
    """Subclass of :class:`Node` that overrides ``weight``.

    Lets a test verify that ``TermMeta`` walks the MRO and that a subclass
    declaration wins over the parent's.
    """

    weight = Declared(value=9)
