"""Nu2 Flow atoms: the Command-composing sub-kind.

Two families:

- **Strategy** - compose mutating atoms directly: ``Sequential`` (``>>``),
  ``Parallel`` (``|``), ``Race`` (``&``), ``Gather``, ``AnyN``. ``Parallel``
  also exposes forced-mode variants ``ParallelThreaded`` / ``ParallelAsync``
  for explicit placement (Race / AnyN are async-only, no variants).
- **Control** - compose bodies under Query parameters: ``IfDo``, ``WhileDo``,
  ``ForeverDo``, ``ForEachDo``, ``ForEachParAsync``, ``ForRangeDo``,
  ``Delay``, ``DelayedDo``, ``SwitchDo``. ``ForEachParAsync`` is the fan-out
  ForEach: one arm per element on the loop, all at once, joining on all.

The flows driven by change subscriptions (``React`` and the rest of the event
kind, ``ReconcileReactive`` and the rest of the level kind, ``Stream``) live in
``nu.core.reactive``, next to the subscriptions they consume.
"""

from .control import (
    Delay,
    DelayedDo,
    ForEachDo,
    ForEachParAsync,
    ForeverDo,
    ForRangeDo,
    IfDo,
    SwitchDo,
    WhileDo,
)
from .noop import Noop
from .parallel import (
    AnyN,
    Gather,
    Parallel,
    ParallelAsync,
    ParallelThreaded,
    Race,
)
from .raise_ import Raise, raise_
from .strategy import Sequential


__all__ = [
    "AnyN",
    "Delay",
    "DelayedDo",
    "ForEachDo",
    "ForEachParAsync",
    "ForRangeDo",
    "ForeverDo",
    "Gather",
    "IfDo",
    "Noop",
    "Parallel",
    "ParallelAsync",
    "ParallelThreaded",
    "Race",
    "Raise",
    "Sequential",
    "SwitchDo",
    "WhileDo",
    "raise_",
]
