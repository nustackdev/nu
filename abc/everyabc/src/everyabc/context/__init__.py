"""Context — execution environment for Terms.

    Context  -- type-keyed handle container
    Handle   -- scoped resource base

Context is passed to Term.execute() providing access to runtime resources.
Handles are the resources themselves (transactions, connections, etc.).
"""

from __future__ import annotations

from .context import Context
from .handle import Handle


__all__ = [
    "Context",
    "Handle",
]
