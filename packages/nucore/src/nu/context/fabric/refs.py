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

    from .queries import FabricExists


__all__ = ["FabricRef"]


class FabricRef(_ContextRef):
    """A Ref into a Context binding, keyed by the fabric type it resolves to.

    The sole child is the address, and it resolves to a type rather than to a
    key: the read looks that type up on the Context and self-yields whatever
    instance is bound there. Nothing is ever written through this Ref -
    instances arrive on the Context from a ``Provide`` bracket, so the value
    side of a ``FabricRef`` is read-only.

    Each concrete fabric gets its own subclass carrying the type it names in
    the ``fabric`` class attribute, which is what the address falls back to
    when none is passed::

        class Solana(FabricRef):
            fabric = SolanaClient

    ``Solana()`` then resolves ``SolanaClient`` from the Context. A bare
    ``FabricRef(SolanaClient)`` still works for the untyped, one-off read.

    Args:
        address: the fabric type to resolve. Defaults to the class's own
            ``fabric`` attribute; a subclass with neither raises at
            construction.

    Notes:
        - This base reads the untagged binding only. Context resolution falls
          back from more tags to fewer, never the other way, so an instance
          bound under ``Provide(..., tag="a")`` is not reachable here. A
          subclass that wants tags stores them itself and forwards them to
          ``ctx.get`` (see ``nu.cluster.refs.RayServiceRef``).
        - A binding holding EMPTY and no binding at all read the same, so use
          ``.exists()`` when the difference matters.
        - The fabric axis is for the long-lived, typed things - storage
          handles, cluster handles, clients. Short-lived scratch values live
          on the attrs axis behind ``AttrRef``.

    Yields:
        The bound instance. EMPTY when the type is not bound.

    Example:
        >>> class Counter:
        ...     def __init__(self, start=0):
        ...         self.n = start
        >>> nu.run(nu.Provide(Counter, {"start": 5}, nu.FabricRef(Counter).exists()))[0]
        True

        >>> nu.run(nu.FabricRef(Counter).exists())[0]
        False
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

    def exists(self) -> FabricExists:
        """A Query yielding whether this Ref's fabric type is bound on the Context.

        Notes:
            - The plain read cannot answer this: an unbound type yields EMPTY
              and so does a type bound to EMPTY.
        """
        from .queries import FabricExists

        return FabricExists(self)
