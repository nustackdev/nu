"""Nu2 Flow atoms: the Command-composing sub-kind.

Two families plus the reactive set:

- **Strategy** - compose mutating atoms directly: ``Sequential`` (``>>``),
  ``Parallel`` (``|``), ``Race`` (``&``), ``Gather``, ``AnyN``. ``Parallel``
  also exposes forced-mode variants ``ParallelThreaded`` / ``ParallelAsync``
  for explicit placement (Race / AnyN are async-only, no variants).
- **Control** - compose bodies under Query parameters: ``IfDo``, ``WhileDo``,
  ``ForeverDo``, ``ForEachDo``, ``ForEachParAsync``, ``ForRangeDo``,
  ``Delay``, ``DelayedDo``, ``SwitchDo``. ``ForEachParAsync`` is the fan-out
  ForEach: one arm per element on the loop, all at once, joining on all.
- **Reactive** - consume change subscriptions and execute bodies in response:
  ``React``, ``ReactWhile``, ``ReactForever``, ``Stream``.
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
from .react import React, ReactForever, ReactWhile
from .strategy import Sequential
from .stream import Stream


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
    "React",
    "ReactForever",
    "ReactWhile",
    "Sequential",
    "Stream",
    "SwitchDo",
    "WhileDo",
    "raise_",
]
