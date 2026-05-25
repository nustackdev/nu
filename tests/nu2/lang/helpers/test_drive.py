"""Unit tests for ``nu2.lang.helpers.drive``.

Covers the drive entries -- value-root (``eval`` / ``aeval`` /
``eval_in_loop``) and stream-root (``first`` / ``collect`` / ``afirst`` /
``alast`` / ``acollect``) -- their Budget lifecycle, async-only refusal
behavior, and stream finalization on short-circuit.
"""

from __future__ import annotations
