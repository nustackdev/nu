"""The Context fabric: the in-memory ``ctx.attrs`` and service bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has two axes:

- attrs - a flat, name-keyed store (``ctx.attrs``) for short-lived primitives
  (loop counters, accumulators, markers). Ref: ``AttrRef``; writes: ``Set`` /
  ``Delete``; existence: ``AttrExists``. The read is ``AttrRef`` itself.
- services - typed bindings (``ctx.bind`` / ``ctx.get``) for execution
  resources. Ref: ``ServiceRef`` (read-only, self-yields); existence:
  ``ServiceExists``.

The read on either axis is the Ref's dual role; only existence needs an
explicit query. Other fabrics (virtuals, mem, substrate) follow the same shape
in their own dirs: a concrete Ref plus the interactions that touch that fabric.
Nothing in ``nu.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .ops import DeleteCommand, SetCommand
from .queries import AttrExistsQuery, ServiceExistsQuery
from .refs import (
    AnyAttrRef,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    DictAttrRef,
    FloatAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    ListAttrRef,
    NoneAttrRef,
    ServiceRef,
    SetAttrRef,
    StrAttrRef,
    TupleAttrRef,
)


__all__ = [
    "AnyAttrRef",
    "AttrExistsQuery",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DeleteCommand",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "NoneAttrRef",
    "ServiceExistsQuery",
    "ServiceRef",
    "SetAttrRef",
    "SetCommand",
    "StrAttrRef",
    "TupleAttrRef",
]
