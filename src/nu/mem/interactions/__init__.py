"""Interactions over the mem fabric: scopes and policies that keep their state in mem.

- ``Frame`` - a fresh dict bound as the mem store for a Shape, for one body.
- ``let`` - a one-slot anonymous frame for a single disposable value.
- ``Throttle`` / ``Debounce`` - rate policies whose state sits in a mem ref
  the caller passes, so it lives exactly as long as the frame that holds it.
"""

from .frame import Frame
from .let import let
from .policy import Debounce, Throttle


__all__ = ["Debounce", "Frame", "Throttle", "let"]
