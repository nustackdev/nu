"""Unit tests for ``nu2.lang.kinds``.

Covers the kind taxonomy -- ``Ref``, ``Interaction`` and its sub-kinds
(``ScalarQuery``, ``StreamQuery``, ``Reduction``, ``Command``, ``Strategy``,
``Control``, ``Span``, ``Bracket``, ``Policy``) -- their declared ``sort``
and ``cardinality`` attributes, the abstract / concrete split, and the
dispatch surface on ``Interaction``.
"""

from __future__ import annotations
