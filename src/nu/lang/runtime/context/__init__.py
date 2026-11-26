"""Nu context - the environment one task runs against.

A Context is a stack of immutable frames holding typed fabric bindings, with
scope tags and optional predicate guards; execution resources and the mem
dicts Shapes read live here.
"""

from .context import Context


__all__ = ["Context"]
