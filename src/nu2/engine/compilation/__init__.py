"""Engine layer: compilation -- ``Term`` -> ``Program`` in three acts.

The phase that turns an immutable Term (description) into a Program
(runnable artifact). Three acts, one verb:

- **index**           -- preorder walk; dense nids; structural columns
  (``terms``, ``children``, ``parent_id``, ``path_of``, ``id_of``).
- **attribute sweeps** -- one pass per computed attribute in schema topo
  order; synthesized leaves-up, inherited root-down.
- **emit**            -- reverse preorder; each Term's ``compile`` /
  ``acompile`` builds a thunk that captures its child thunks.

Output is a Program: the indexed Term plus attribute and thunk columns,
ready for a Runtime to drive. No IR, no optimizer.
"""

from .attribution import sweep_attributes
from .compile import compile
from .emit import emit_thunks
from .index import build_index
from .program import Path, Program, UnknownAttributeError


__all__ = [
    "Path",
    "Program",
    "UnknownAttributeError",
    "build_index",
    "compile",
    "emit_thunks",
    "sweep_attributes",
]
