"""Flow Commands -- imperative mutations composing sub-flows.

`IfDo`, `Race`, `Parallel` (was `ParAll`), and `ForEachDo` (was
`ForEach`) live in `nu.terms.flow` (new core); they're not re-exported
here. Top-level `nu.IfDo` / `nu.Race` / `nu.Parallel` / `nu.ForEachDo`
resolve there.
"""

from .control import DoWhile, Forever, SwitchDo, While
from .error import Retry, TryCatch
from .iteration import (
    Filter,
    Find,
    FindIndex,
    GroupBy,
    Map,
    Partition,
    TakeWhile,
    ToDict,
    UniqueDo,
)
from .iteration_range import ForRange
from .parallel import ParAny
from .timing import Debounce, Throttle, Timed, Timeout


__all__ = [
    "Debounce",
    "DoWhile",
    "Filter",
    "Find",
    "FindIndex",
    "ForRange",
    "Forever",
    "GroupBy",
    "Map",
    "ParAny",
    "Partition",
    "Retry",
    "SwitchDo",
    "TakeWhile",
    "Throttle",
    "Timed",
    "Timeout",
    "ToDict",
    "TryCatch",
    "UniqueDo",
    "While",
]
