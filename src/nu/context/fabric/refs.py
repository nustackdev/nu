"""``FabricRef``: a Ref into a Context binding.

Every ctx-bound thing is a Fabric (the empty marker Protocol). A ``FabricRef``
names one by its resolved address (the fabric type). The read is the dual role:
self-yield the bound fabric (``EMPTY`` when unbound). Fabrics are bound on the
Context, not written through a Ref, so ``FabricRef`` is read-only *as a value*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .queries import FabricExistsQuery


__all__ = ["FabricRef"]


class FabricRef(_ContextRef):
    """A Ref into a Context binding, keyed by its resolved address.

    The address resolves to a fabric type; the read self-yields the bound
    fabric (``EMPTY`` when unbound). Fabrics are bound on the Context, not
    written through a Ref.

    Each concrete fabric gets its own ``FabricRef`` subclass carrying the
    bound fabric type in the ``fabric`` class attribute::

        class Solana(FabricRef):
            fabric = SolanaClient
            slot = method_query(IntForm, "getSlot")

    ``Solana()`` then resolves ``SolanaClient`` from the Context, and its
    methods (built by the ``method_*`` descriptors / ``MethodFactory``)
    serialize against each other while staying independent of any other
    fabric. A bare ``FabricRef(SolanaClient)`` still works for the untyped,
    one-off read.
    """

    fabric: ClassVar[type | None] = None

    def __init__(self, address: object = None) -> None:
        if address is None:
            address = type(self).fabric
            if address is None:
                msg = f"{type(self).__name__} has no bound fabric; pass one or set `fabric`"
                raise TypeError(msg)
        super().__init__(address)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric = children[0]

        def thunk(rt: Runtime) -> object:
            f = fabric(rt)
            return rt.ctx.get(f) if rt.ctx.has(f) else EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric = children[0]

        async def athunk(rt: Runtime) -> object:
            f = await fabric(rt)
            return rt.ctx.get(f) if rt.ctx.has(f) else EMPTY

        return athunk

    def exists(self) -> FabricExistsQuery:
        """A Query yielding whether this Ref's fabric type is bound."""
        from .queries import FabricExistsQuery

        return FabricExistsQuery(self)
