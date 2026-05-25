"""Unit tests for ``nu2.lang.helpers._guard``.

Covers ``refuse_async_only`` -- it reads the root's
``HAS_ASYNC_ONLY_ATOM`` column and raises a clear RuntimeError pointing
the caller at the async sibling.
"""

from __future__ import annotations
