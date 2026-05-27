"""Flow atoms: the Interactions that compose Commands.

Seq and Par are Strategies - they hold Commands directly; Par declares a
parallel exec order. If and While are Controls - they hold Commands under a
Query condition.
"""

from __future__ import annotations

from nu2.engine.structure import Declared
from nu2.lang import Control, ExecOrder, Strategy


__all__ = ["If", "Par", "Seq", "While"]


class Seq(Strategy):
    """Runs its Command children one after another."""


class Par(Strategy):
    """Runs its Command children in parallel."""

    exec_order = Declared(value=ExecOrder.PARALLEL)


class If(Control):
    """Runs its body Commands once when a Query condition holds.

    Slot 0 is the param (the yielding condition); slot 1+ are body
    (mutating children).
    """

    param_slots = Declared(value=frozenset({0}))


class While(Control):
    """Repeats its body Commands while a Query condition holds.

    Slot 0 is the param (the yielding condition); slot 1+ are body
    (mutating children).
    """

    param_slots = Declared(value=frozenset({0}))
