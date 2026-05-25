"""Unit tests for ``nu2.lang.runtime.runtime``.

Covers ``Runtime`` -- the concrete Runtime that drives compiled Programs.
Dispatch (``eval`` / ``aeval``), sequential and parallel helpers, stream
pumps, sentinel propagation, hybrid async pump, and the
boundary helpers (``in_thread`` / ``a_in_thread``).
"""

from __future__ import annotations
