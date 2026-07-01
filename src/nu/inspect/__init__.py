"""nu.inspect -- inspection tools for Nu trees and Shapes.

Three families, no web anything:

- **render** (``render_nu``) - print a Nu tree as an ANSI or plain box-tree, one
  node per line, each kind color coded.
- **shape** (``render_shape``) - print a Shape + its backing storage as an ANSI
  or plain tree, walking ``Shape._slots`` and rendering the data behind them.
- **annotate** (``annotate_steps`` / ``annotate_retries`` / ``set_logger_name``)
  - structural rewrites that layer logging onto a tree without changing what it
  computes, all output through the stderr side of the stdio fabric.

There is deliberately no HTML explorer here - just the two tree printers and the
logging rewrites.
"""

from __future__ import annotations

from nu.inspect.annotate import annotate_retries, annotate_steps, set_logger_name
from nu.inspect.render import render_nu
from nu.inspect.shape import render_shape


__all__ = [
    "annotate_retries",
    "annotate_steps",
    "render_nu",
    "render_shape",
    "set_logger_name",
]
