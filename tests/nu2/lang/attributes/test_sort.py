"""Unit tests for ``nu2.lang.attributes.sort``.

Covers the ``Sort`` enum (structural categories), the composition
``MATRIX`` (allowed child sorts per parent sort), ``subsort`` traversal,
``matrix_sort`` folding, and the synthesized ``has_command`` flag.
"""

from __future__ import annotations
