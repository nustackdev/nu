"""Span atoms: the transparent Interactions that govern a body.

Scope is a Bracket - it wraps a body in setup and teardown. Retry is a Policy -
it re-runs a failing body. Both yield whatever their body yields.
"""

from __future__ import annotations

from nu2.lang import Bracket, Policy


__all__ = ["Retry", "Scope"]


class Scope(Bracket):
    """Wraps a body in setup before and teardown after."""


class Retry(Policy):
    """Re-runs its body on failure, up to a payload-carried limit."""
