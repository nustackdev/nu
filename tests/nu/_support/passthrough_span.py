"""Passthrough Span shapes for scheduling/placement tests.

A bare :class:`nu.lang.Bracket` cannot drive - Span's base ``_aeval`` raises
``NotImplementedError``. Scheduling-shape tests only need Span **transparency**
over a body: run the body, forward its value, no lifecycle work. This module
provides that minimum.

The core ships ``nu.spans.bracket._LifecycleBracket`` whose default ``_open``
is a straight passthrough, so subclassing it gives a genuine passthrough
Bracket for free.
"""

from __future__ import annotations

from nu.spans.bracket import _LifecycleBracket


__all__ = ["PassBracket"]


class PassBracket(_LifecycleBracket):
    """A Bracket that opens no boundary - runs its body straight through."""
