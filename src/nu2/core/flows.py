"""Flow atoms: the Interactions that compose Commands.

Seq and Par are Strategies - they hold Commands directly; Par declares a
parallel exec order. If and While are Controls - they hold Commands under a
Query condition.
"""

from __future__ import annotations

from nu2.engine.structure import Attribute
from nu2.lang import Control, ExecOrder, Strategy


__all__ = ["If", "Par", "Seq", "While"]


class Seq(Strategy):
    """Runs its Command children one after another."""


class Par(Strategy):
    """Runs its Command children in parallel."""

    exec_order = Attribute.declared(ExecOrder.PARALLEL)


class If(Control):
    """Runs its body Commands once when a Query condition holds."""


class While(Control):
    """Repeats its body Commands while a Query condition holds."""
