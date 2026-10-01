"""The Context fabric: the in-memory ``ctx.attrs`` and fabric bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has two axes:

- **attrs** - the channel an interaction uses to hand its internal values
  to its body (``ctx.attrs``): a loop its item, a catch the error. Only
  interactions bind it; the tree reads it with ``Attr(name)`` and asks
  ``Attr(name).exists()`` (a ``Bool`` over ``AttrExists``). It is never a store: state goes through a fabric.
- **fabric** - typed bindings (``ctx.bind`` / ``ctx.get``) for every other
  ctx-bound thing: execution resources, storage handles, cluster handles,
  compute actors. Ref: ``FabricRef`` (read-only, self-yields); existence:
  ``.exists()``, a ``Bool`` over ``FabricExists``. Provisioning brackets
  ``Provide`` / ``ProvideList`` / ``ProvideDict`` install fabrics into the
  Context for a body's duration.
  Protocols ``Fabric`` (empty marker; every ctx-bound thing satisfies it) and
  ``FabricLifecycle(Fabric)`` (with optional setup / cleanup) describe the
  contract.

The read on the attrs axis is the Ref's dual role; only existence needs an
explicit query. Other concrete fabrics (``nu.mem`` in the kernel, the rest in
``nustd``) follow the same shape in their own dirs: concrete Refs plus the
interactions that touch that fabric. Nothing in ``nu.core`` touches a fabric -
core is the pure Python builtins.
"""

from __future__ import annotations

from .attrs import Attr, AttrExists
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
    "Attr",
    "AttrExists",
    "Fabric",
    "FabricExists",
    "FabricLifecycle",
    "FabricRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "With",
]
