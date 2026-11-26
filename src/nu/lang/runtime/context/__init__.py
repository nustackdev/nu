"""Nu context - the environment one task runs against.

A Context is a stack of immutable frames holding typed fabric bindings, with
scope tags and optional predicate guards; execution resources and mem dicts
live here. ``ctx.attrs`` (a flat name store) stays until task-184 phase 4.
"""

from .attributes import Attributes
from .context import Context


__all__ = ["Attributes", "Context"]
