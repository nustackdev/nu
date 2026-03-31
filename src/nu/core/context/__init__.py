"""Context -- execution environment for Terms.

    Context     -- tagged value store
    Attributes  -- flat mutable key-value store for primitive data

Context is passed to Term.execute() providing access to runtime resources.
"""

from __future__ import annotations

from .attributes import Attributes
from .context import Context


__all__ = [
    "Attributes",
    "Context",
]
