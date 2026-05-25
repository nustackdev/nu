"""Unit tests for ``nu2.lang.attributes.cardinality``.

Covers the ``Cardinality`` enum (SCALAR / STREAM / VOID / TRANSPARENT),
the synthesized ``CARDINALITY`` fold across the tree, and the
TRANSPARENT-pass-through rule for ``Span`` subtrees.
"""

from __future__ import annotations
