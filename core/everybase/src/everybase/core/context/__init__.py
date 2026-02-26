"""Context — execution environment for Terms.

    Context  -- tagged value store

Context is passed to Term.execute() providing access to runtime resources.
"""

from __future__ import annotations

from .context import Context


__all__ = [
    "Context",
]
