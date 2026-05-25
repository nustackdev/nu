"""Command atoms: the Interactions that write the Context.

Each declares ``own_effects``: slot 0 holds the Ref it writes. Every other
slot binds in read role, so ``Set(Ref("a"), Add(Ref("b"), Literal(1)))`` tracks
one write of ``a`` and one read of ``b``.
"""

from __future__ import annotations

from nu2.engine.structure import Declared
from nu2.lang import Command, Effect


__all__ = ["Delete", "Emit", "Set"]


class Set(Command):
    """Writes the value of slot 1 to the Ref in slot 0."""

    own_effects = Declared(value={0: Effect.WRITE})


class Delete(Command):
    """Removes the Ref in slot 0 from the Context."""

    own_effects = Declared(value={0: Effect.WRITE})


class Emit(Command):
    """Appends the value of slot 1 to the stream Ref in slot 0."""

    own_effects = Declared(value={0: Effect.WRITE})
