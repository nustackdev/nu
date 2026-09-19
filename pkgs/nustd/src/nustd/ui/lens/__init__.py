"""nustd.ui.lens -- any Nu Shape, browsable as cascading columns.

A package beside ``core`` and ``nudle`` rather than a module inside ``refs``:
``refs`` holds widgets, and this is a widget plus the two pieces of machinery
that make it worth having.

- :mod:`.ref`      -- ``LensRef``, the surface. Frames in, frames out.
- :mod:`.columns`  -- what a Shape and a cursor are worth as columns. The walk.
- :mod:`.presets`  -- ``browse``, the whole thing assembled and ready to run.

``ref`` and ``columns`` import no fabric; ``presets`` imports ``nustd.kv``,
because placing the storage boundary is exactly the job it exists to do. See
its docstring for why that line is where it is.

Everything is reached through this package and nothing is re-exported flat,
``LensRef`` included: a lens is a subsystem rather than a widget, so one name
holds all of it and a reader who has found ``nustd.ui.lens`` has found the
whole thing. ``nustd.ui.lens.LensRef``, ``nustd.ui.lens.browse``,
``nustd.ui.lens.columns``. That last name does double duty, as the module and
as the builder it exports; the builder wins on the package, which is the one
people call.
"""

from __future__ import annotations

from .columns import DEFAULT_MAX_ROWS, column_terms, columns
from .presets import browse
from .ref import LensRef


__all__ = [
    "DEFAULT_MAX_ROWS",
    "LensRef",
    "browse",
    "column_terms",
    "columns",
]
