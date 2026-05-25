"""Nu's validity layer: laws and the predicates they're written from.

- ``predicates`` - the scope/holds building blocks (``of_sort``, ``composes``,
  ``ref_slots_hold_refs``, ...).
- ``laws``       - the ``LAWS`` tuple: every rule an attributed Nu program
  must satisfy.

Feed ``LAWS`` to ``gate`` for a verdict or to ``validate`` for a rejection.
"""

from __future__ import annotations

from .laws import LAWS


__all__ = ["LAWS"]
