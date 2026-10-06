"""nustd.ui.table -- a table whose rows are what the store holds.

A package beside ``lens`` rather than a module in ``refs``: ``TableRef`` is the
widget and stays in ``refs``; this is the machinery that binds one to a store.

- :mod:`.values`   -- the rules, plain Python over plain values: how a typed
                      value is stored, how rows sort, what a fresh column is.
- :mod:`.presets`  -- ``Row``, the stored row, and ``sync``, a table kept equal
                      to its store, live across tabs.

``values`` imports no fabric; ``presets`` imports ``nustd.kv``, because placing
the storage boundary is the job it exists to do. See its docstring for the
layout and why the line is where it is.
"""

from __future__ import annotations

from .presets import REPAINT_DELAY, Row, sync
from .values import blank, coerce


__all__ = ["REPAINT_DELAY", "Row", "blank", "coerce", "sync"]
