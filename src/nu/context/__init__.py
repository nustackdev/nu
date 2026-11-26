"""The Context fabric: typed fabric bindings on the Context's frames.

A Fabric is an addressable space where Refs live; it resolves Refs and carries
out the Interactions over them. The Context holds them as typed bindings
(``ctx.bind`` / ``ctx.get``) for every ctx-bound thing: execution resources,
storage handles, cluster handles, compute actors, the mem dicts Shapes read.
Ref: ``FabricRef`` (read-only, self-yields); existence: ``.exists()``, a
``Bool`` over ``FabricExists``. Provisioning brackets ``Provide`` /
``ProvideList`` / ``ProvideDict`` push fabrics onto the Context for a body's
duration. A provided fabric subclasses ``Fabric``, the base class carrying
setup / cleanup with no-op defaults.

Values a parent hands its body never go here by name: they go through mem
(``nu.let`` and the bindings in ``nu.lang.binding``). Other concrete fabrics
(``nu.mem`` in the kernel, the rest in ``nustd``) follow the same shape in
their own dirs: concrete Refs plus the interactions that touch that fabric.
Nothing in ``nu.core`` touches a fabric - core is the pure Python builtins.
"""

from __future__ import annotations

from .fabric import (
    Fabric,
    FabricExists,
    FabricRef,
    Provide,
    ProvideDict,
    ProvideList,
    With,
)


__all__ = [
    "Fabric",
    "FabricExists",
    "FabricRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "With",
]
