"""Interactions over the mem fabric: scopes and policies that keep their state in mem.

- ``let`` - a fresh mem frame for a body, over a Shape or one generated from a lambda.
- ``Throttle`` / ``Debounce`` - rate policies whose state sits in a mem ref
  the caller passes, so it lives exactly as long as the frame that holds it.
"""

from .let import let
from .policy import Debounce, Throttle


__all__ = ["Debounce", "Throttle", "let"]
