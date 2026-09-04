"""The Context fabric: the in-memory ``ctx.attrs`` and fabric bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has two axes:

- **attrs** - a flat, name-keyed store (``ctx.attrs``) for short-lived
  primitives (loop counters, accumulators, markers). Ref: ``AttrRef``; writes:
  ``SetCmd`` / ``Delete``; existence: ``AttrExists``. The read
  is ``AttrRef`` itself.
- **fabric** - typed bindings (``ctx.bind`` / ``ctx.get``) for every other
  ctx-bound thing: execution resources, storage handles, cluster handles,
  compute actors. Ref: ``FabricRef`` (read-only, self-yields); existence:
  ``FabricExists``. Provisioning brackets ``Provide`` / ``ProvideList`` /
  ``ProvideDict`` install fabrics into the Context for a body's duration.
  Protocols ``Fabric`` (empty marker; every ctx-bound thing satisfies it) and
  ``FabricLifecycle(Fabric)`` (with optional setup / cleanup) describe the
  contract.

The read on the attrs axis is the Ref's dual role; only existence needs an
explicit query. Other concrete fabrics (virtuals, mem, ray, ...) follow the
same shape in their own dirs: concrete Refs plus the interactions that touch
that fabric. Nothing in ``nu.core`` touches a fabric - core is the pure Python
builtins.
"""

from __future__ import annotations

from .attrs import (
    AnyAttrRef,
    AttrExists,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    Delete,
    DictAttrRef,
    FloatAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    Let,
    ListAttrRef,
    NoneAttrRef,
    SetAttrRef,
    SetCmd,
    StrAttrRef,
    TupleAttrRef,
)
from .fabric import (
    Fabric,
    FabricExists,
    FabricLifecycle,
    FabricRef,
    Provide,
    ProvideDict,
    ProvideList,
    With,
)


__all__ = [
    "AnyAttrRef",
    "AttrExists",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "Delete",
    "DictAttrRef",
    "Fabric",
    "FabricExists",
    "FabricLifecycle",
    "FabricRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "Let",
    "ListAttrRef",
    "NoneAttrRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "SetAttrRef",
    "SetCmd",
    "StrAttrRef",
    "TupleAttrRef",
    "With",
]
