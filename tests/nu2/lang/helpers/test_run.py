"""Unit tests for ``nu2.lang.helpers.run``.

Covers the all-in-one entries (``run`` / ``arun`` / ``run_in_loop``):
that they compile, validate, and drive in one call; that validation
failures surface; that the async-only refusal in ``run`` matches the
underlying drive guard.
"""

from __future__ import annotations
