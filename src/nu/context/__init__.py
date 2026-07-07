"""The Context fabric: the in-memory ``ctx.attrs`` and service bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has three axes:

- **attrs** - a flat, name-keyed store (``ctx.attrs``) for short-lived
  primitives (loop counters, accumulators, markers). Ref: ``AttrRef``; writes:
  ``SetCommand`` / ``DeleteCommand``; existence: ``AttrExistsQuery``. The read
  is ``AttrRef`` itself.
- **services** - typed bindings (``ctx.bind`` / ``ctx.get``) for execution
  resources. Ref: ``ServiceRef`` (read-only, self-yields); existence:
  ``ServiceExistsQuery``; in-tree method calls: the ``method`` descriptor /
  ``MethodFactory`` (a service-flavored ``InteractionFactory``).
- **fabric** - lifecycle interactions that provision resources into the
  Context for a body's duration. Brackets: ``Provide`` / ``ProvideList`` /
  ``ProvideDict``. Protocols: ``Resource`` (setup / cleanup) and ``Fabric``
  (a Resource that hosts its own Refs, e.g. Ray, Invisibles).

The read on either data axis is the Ref's dual role; only existence needs an
explicit query. Other fabrics (virtuals, mem, ray, ...) follow the same shape
in their own dirs: concrete Refs plus the interactions that touch that fabric.
Nothing in ``nu.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .attrs import (
    AnyAttrRef,
    AttrExistsQuery,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    DeleteCommand,
    DictAttrRef,
    FloatAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    ListAttrRef,
    NoneAttrRef,
    SetAttrRef,
    SetCommand,
    StrAttrRef,
    TupleAttrRef,
)
from .fabric import Fabric, Provide, ProvideDict, ProvideList, Resource
from .services import ServiceExistsQuery, ServiceRef


__all__ = [
    "AnyAttrRef",
    "AttrExistsQuery",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DeleteCommand",
    "DictAttrRef",
    "Fabric",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "NoneAttrRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "Resource",
    "ServiceExistsQuery",
    "ServiceRef",
    "SetAttrRef",
    "SetCommand",
    "StrAttrRef",
    "TupleAttrRef",
]
