"""Unit tests for ``nu2.lang.runtime.context.context``.

Covers ``Context`` -- the tagged value store the Runtime drives against.
Immutability across ``bind`` / ``lazy``, resolution by type then scope tags
with subset fallback, and predicate-guarded ``get``.
"""

from __future__ import annotations
