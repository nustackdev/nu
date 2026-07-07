"""Nu2 Flow atoms: the Command-composing sub-kind.

Two families plus the reactive set:

- **Strategy** - compose mutating atoms directly: ``Sequential`` (``>>``),
  ``Parallel`` (``|``), ``Race`` (``&``), ``Gather``, ``AnyN``.
- **Control** - compose bodies under Query parameters: ``IfDo``, ``WhileDo``,
  ``ForeverDo``, ``ForEachDo``, ``ForRangeDo``, ``Delay``, ``DelayedDo``,
  ``SwitchDo``.
- **Reactive** - consume change subscriptions and execute bodies in response:
  ``React``, ``ReactWhile``, ``ReactForever``, ``Stream``.
"""

from .control import (
    Delay,
    DelayedDo,
    ForEachDo,
    ForeverDo,
    ForRangeDo,
    IfDo,
    SwitchDo,
    WhileDo,
)
from .noop import Noop
from .raise_ import Raise, raise_
from .react import React, ReactForever, ReactWhile
from .strategy import AnyN, Gather, Parallel, Race, Sequential
from .stream import Stream


__all__ = [
    "AnyN",
    "Delay",
    "DelayedDo",
    "ForEachDo",
    "ForRangeDo",
    "ForeverDo",
    "Gather",
    "IfDo",
    "Noop",
    "Parallel",
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
