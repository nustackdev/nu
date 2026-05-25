"""Unit tests for ``nu2.lang.attributes.execution``.

Covers the ``ExecOrder`` enum, declared / synthesized async-related
attributes (``REQUIRES_ASYNC``, ``ASYNC_AFFINITY``, ``HAS_ASYNC_ONLY_ATOM``,
``ON_LOOP``), and the inherited ``EXEC_ORDER`` threading.
"""

from __future__ import annotations
