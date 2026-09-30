"""The Context fabric: the in-memory ``ctx.attrs`` and fabric bindings.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context fabric has two axes:

- **attrs** - a flat, name-keyed store (``ctx.attrs``) for short-lived
  values (loop counters, accumulators, markers). ``Let`` declares a name;
  the typed refs (``IntRef``, ``StrRef``, ..., ``ObjectRef``) read it,
  ``ref.set(v)`` reassigns it and ``ref.exists()`` asks whether it is declared.
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

from .attrs import AttrRef as AttrRef  # internal base, not in __all__
from .attrs import (
    BoolRef,
    BytesRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    Let,
    ObjectRef,
    StrRef,
    TupleRef,
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
    "BoolRef",
    "BytesRef",
    "Fabric",
    "FabricExists",
    "FabricLifecycle",
    "FabricRef",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "Let",
    "ObjectRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "StrRef",
    "TupleRef",
    "With",
]
