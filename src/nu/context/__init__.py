"""The Context's fabric bindings: typed, long-lived state on immutable frames.

The Context is a stack of immutable frames holding fabric bindings. A Fabric
is an addressable space where Refs live; it resolves Refs and carries out the
Interactions over them. Every ctx-bound thing is a fabric binding
(``ctx.bind`` / ``ctx.get``): execution resources, storage handles, cluster
handles, compute actors, the mem dicts Shapes read.

- ``fabric`` - ``Fabric``, the base class of a declared fabric: setup /
  cleanup (sync and async) with no-op defaults, and the ``async_only`` flag.
- ``refs`` - ``FabricRef``, a read-only Ref that self-yields the bound fabric
  (``NULL`` when unbound). Subclass and set ``fabric = SomeFabric`` to name a
  typed binding.
- ``queries`` - ``FabricExists``, the explicit existence check behind
  ``FabricRef.exists()``, since a bound ``NULL`` reads like no binding.
- ``provide`` - ``Provide`` / ``ProvideList`` / ``ProvideDict`` / ``With``,
  the Brackets that construct fabrics on entry, bind them on ctx for the
  body's duration, and tear them down in reverse on exit.

Values a parent hands its body never go here by name: they go through mem
(``nu.let`` and the bindings in ``nu.lang.binding``). Other concrete fabrics
(``nu.mem`` in the kernel, the rest in ``nustd``) follow the same shape in
their own dirs: concrete Refs plus the interactions that touch that fabric.
Nothing in ``nu.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .fabric import Fabric
from .provide import Provide, ProvideDict, ProvideList, With
from .queries import FabricExists
from .refs import FabricRef


__all__ = [
    "Fabric",
    "FabricExists",
    "FabricRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "With",
]
