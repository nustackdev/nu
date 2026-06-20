"""The Context fabric: the in-memory ``ctx.attrs`` addressable space.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric is the simplest one: a flat,
name-keyed store (``ctx.attrs``) for short-lived primitives - loop counters,
accumulators, markers. It owns its Ref (``AttrRef``) and its write
interactions (``Set``, ``Delete``); the read is ``AttrRef`` itself.

Other fabrics (virtuals, mem, substrate) follow the same shape in their own
dirs: a concrete Ref plus the interactions that touch that fabric. Nothing in
``nu2.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .ops import Delete, Set
from .refs import AttrRef


__all__ = ["AttrRef", "Delete", "Set"]
