"""``ServiceRef``: a Ref into the Context service bindings.

A service is a typed binding on the Context (``ctx.bind(SolanaClient, client)``).
``ServiceRef`` names it by resolved address (the service type). The read is the
dual role: self-yield the bound service (EMPTY when unbound). Services are
bound on the Context, not written through a Ref, so ``ServiceRef`` is
read-only *as a value*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .queries import ServiceExistsQuery


__all__ = ["ServiceRef"]


class ServiceRef(_ContextRef):
    """A Ref into the Context service bindings, keyed by its resolved address.

    The address resolves to a service type; the read self-yields the bound
    service (EMPTY when unbound). Services are bound on the Context, not
    written through a Ref.

    A service is a fabric, and each fabric is one concrete Ref class - so a
    service gets its own ``ServiceRef`` subclass carrying the bound service
    type in the ``service`` class attribute::

        class Solana(ServiceRef):
            service = SolanaClient
            slot = method_query(IntForm, "getSlot")

    ``Solana()`` then resolves ``SolanaClient`` from the Context, and its
    methods (built by the ``method_*`` descriptors / ``MethodFactory``)
    serialize against each other while staying independent of any other
    service. A bare ``ServiceRef(SolanaClient)`` still works for the untyped,
    one-off read.
    """

    service: ClassVar[type | None] = None

    def __init__(self, address: object = None) -> None:
        if address is None:
            address = type(self).service
            if address is None:
                msg = f"{type(self).__name__} has no bound service; pass one or set `service`"
                raise TypeError(msg)
        super().__init__(address)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        service = children[0]

        def thunk(rt: Runtime) -> object:
            svc = service(rt)
            return rt.ctx.get(svc) if rt.ctx.has(svc) else EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        service = children[0]

        async def athunk(rt: Runtime) -> object:
            svc = await service(rt)
            return rt.ctx.get(svc) if rt.ctx.has(svc) else EMPTY

        return athunk

    def exists(self) -> ServiceExistsQuery:
        """A Query yielding whether this Ref's service type is bound."""
        from .queries import ServiceExistsQuery

        return ServiceExistsQuery(self)
