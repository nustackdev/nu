"""Nu context - runtime resource container.

Two axes:

- ``ctx.attrs`` - flat key-value store; Refs read and write here.
- ``ctx.bind`` / ``ctx.get`` - typed service bindings with scope tags and
  optional predicate guards; execution resources live here.

Typed Refs (AttrRef, ServiceRef and their Form-mixed variants) and their
ScalarQuery ops are deferred until the Form layer lands in nu.
"""

from .attributes import Attributes
from .context import Context


__all__ = ["Attributes", "Context"]
