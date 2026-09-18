"""nu.factory - atom builders on top of the language essentials.

A builder layer, not part of ``nu.lang`` core. Everything here takes a
Python callable and produces a real ``Nu`` subclass ready to slot into a
tree. ``nu.core`` atoms stay hand-written end-to-end for the hot path;
the factory is for the rest.

- **core** - ``InteractionFactory``, the generic mechanism everything else
  builds on. Takes any callable + base kind.
- **host** - the ``@host`` decorator, minimum-ceremony over
  ``InteractionFactory``. Defaults the base kind to ``ScalarQuery`` so
  wrapping a pure function is a one-liner.
"""

from __future__ import annotations

from .core import InteractionFactory
from .host import host


__all__ = [
    "InteractionFactory",
    "host",
]
