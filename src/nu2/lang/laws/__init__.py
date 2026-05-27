"""Nu's validity layer: laws and the predicates they're written from.

- ``predicates`` - the generic scope/holds combinators (``of_sort``,
  ``attr_true``, ``declares_effect``, ...).
- one module per *dimension* of validity: ``composition``, ``effects``,
  ``cardinality``, ``execution``, ``observability``, ``refs``, ``spans``.
  Each owns its dimension-specific helpers and its ``LAWS`` tuple.
- ``LAWS`` - the full set, concatenated from every dimension.

Feed ``LAWS`` to ``gate`` for a verdict or to ``validate`` for a rejection.
"""

from __future__ import annotations

from . import cardinality, composition, effects, execution, observability, refs, spans


__all__ = ["LAWS"]


LAWS = (
    *composition.LAWS,
    *effects.LAWS,
    *cardinality.LAWS,
    *execution.LAWS,
    *observability.LAWS,
    *refs.LAWS,
    *spans.LAWS,
)
