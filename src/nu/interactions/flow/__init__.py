"""Flow interactions - concrete Strategy and Control kinds.

Generic Flows (Sequential, Parallel, Race, Gather, IfDo, ForEachDo,
WhileDo) live in `nu.terms.flow`. This package adds domain-specific
subclasses.
"""

from .control import DoWhile, Forever, SwitchDo, While
from .iter_each import ForEach
from .iteration_range import ForRange
from .strategy import ParAny


__all__ = [
    "DoWhile",
    "ForEach",
    "ForRange",
    "Forever",
    "ParAny",
    "SwitchDo",
    "While",
]
