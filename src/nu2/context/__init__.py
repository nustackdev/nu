"""The Context fabric: the in-memory ``ctx.attrs`` and service bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has two axes, both ported
one-for-one from v1:

- attrs - a flat, name-keyed store (``ctx.attrs``) for short-lived primitives
  (loop counters, accumulators, markers). Ref: ``AttrRef``; writes: ``Set`` /
  ``Delete``; existence: ``AttrExists``. The read is ``AttrRef`` itself.
- services - typed bindings (``ctx.bind`` / ``ctx.get``) for execution
  resources. Ref: ``ServiceRef`` (read-only, self-yields); existence:
  ``ServiceExists``.

The read on either axis is the Ref's dual role; only existence needs an
explicit query. Other fabrics (virtuals, mem, substrate) follow the same shape
in their own dirs: a concrete Ref plus the interactions that touch that fabric.
Nothing in ``nu2.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .ops import Delete, Set
from .queries import AttrExists, ServiceExists
from .refs import AttrRef, ServiceRef


__all__ = ["AttrExists", "AttrRef", "Delete", "ServiceExists", "ServiceRef", "Set"]
