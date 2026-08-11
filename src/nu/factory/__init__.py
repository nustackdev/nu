"""nu.factory - atom builders on top of the language essentials.

A builder layer, not part of ``nu.lang`` core. Everything here takes a
Python callable and produces a real ``Nu`` subclass ready to slot into a
tree. ``nu.core`` atoms stay hand-written end-to-end for the hot path;
the factory is for the rest.

- **core** - ``InteractionFactory``, the generic mechanism everything else
  builds on. Takes any callable + base kind.
- **functions** - ``ScalarQueryFactory``, the kind-fixed convenience for
  turning a pure function into a ``ScalarQuery`` atom.
- **host** - the ``@host`` decorator, minimum-ceremony over
  ``InteractionFactory``.
"""

from __future__ import annotations

from .core import InteractionFactory
from .functions import ScalarQueryFactory
from .host import host


__all__ = [
    "InteractionFactory",
    "ScalarQueryFactory",
    "host",
]
