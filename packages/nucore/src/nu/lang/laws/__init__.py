"""Nu's validity layer: laws and the predicates they're written from.

- ``predicates`` - the generic scope/holds combinators (``of_sort``,
  ``attr_true``, ``cardinality_is``, ...).
- one module per *dimension* of validity: ``composition``, ``effects``,
  ``cardinality``, ``execution``, ``observability``, ``dyn``, ``refs``,
  ``spans``.
  Each owns its dimension-specific helpers and its ``LAWS`` tuple.
- ``LAWS`` - the mutable full set, concatenated from every dimension.
  Non-lang layers (e.g. ``nu.core.flows.parallel``) extend this list at import
  time; callers should read it live (do not cache a copy).

Feed ``LAWS`` to ``gate`` for a verdict or to ``validate`` for a rejection.
"""

from __future__ import annotations

from . import (
    cardinality,
    composition,
    effects,
    execution,
    observability,
    refs,
    spans,
)


__all__ = ["LAWS"]


# LAWS is a mutable list, not a tuple, so subsystems that layer on Nu can
# register additional laws at import time (see ``nu.core.flows.parallel``). Every
# caller reads it live.
LAWS: list = [
    *composition.LAWS,
    *effects.LAWS,
    *cardinality.LAWS,
    *execution.LAWS,
    *observability.LAWS,
    *refs.LAWS,
    *spans.LAWS,
]
