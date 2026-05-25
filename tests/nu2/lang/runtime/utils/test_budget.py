"""Unit tests for ``nu2.lang.runtime.utils.budget``.

Covers ``Budget`` -- per-execution resources. Cheap construction at
``max_parallel == 1``, thread-pool allocation otherwise, async semaphore
in async mode, idempotent close.
"""

from __future__ import annotations
