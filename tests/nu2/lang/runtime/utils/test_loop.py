"""Unit tests for ``nu2.lang.runtime.utils.loop``.

Covers ``into_loop`` (sync->async bridge: runs a coroutine to completion,
spinning a fresh loop when needed) and ``safely_closing`` /
``safely_aclosing`` (idempotent close on iterables with optional ``close``
/ ``aclose``).
"""

from __future__ import annotations
