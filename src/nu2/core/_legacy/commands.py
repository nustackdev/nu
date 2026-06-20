"""Command atoms: the Interactions that write the Context.

Each declares ``mutates``: the slot indices it writes to (slot 0 holds the Ref
it writes). Every other slot binds in read role, so
``Set(Ref("a"), Add(Ref("b"), Literal(1)))`` tracks one write of ``a`` and one
read of ``b``.
"""

from __future__ import annotations

from nu2.engine.structure import Declared
from nu2.lang import Command


__all__ = ["Delete", "Emit", "Set"]


class Set(Command):
    """Writes the value of slot 1 to the Ref in slot 0."""

    mutates = Declared(value=frozenset({0}))


class Delete(Command):
    """Removes the Ref in slot 0 from the Context."""

    mutates = Declared(value=frozenset({0}))


class Emit(Command):
    """Appends the value of slot 1 to the stream Ref in slot 0."""

    mutates = Declared(value=frozenset({0}))
