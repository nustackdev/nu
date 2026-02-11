"""ServiceRef and Service — service refs and declarative access.

Two-part design (like Shape / ShapeRef in eb-shape):

    ServiceRef  — ref term that lives in expression trees.
                  Resolves a service client from context via SERVICE_CLS.
                  Full Ref — can hold method descriptors directly.

    Service     — declarative entry point users subclass.
                  Holds method() descriptors, never instantiated.
                  Creates a ServiceRef subclass behind the scenes.

Direct ServiceRef usage (imperative)::

    class SolanaRef(ServiceRef):
        SERVICE_CLS = SolanaClient
        get_slot = method(IntValue, "getSlot")

    SolanaRef.get_slot()          # class-level access (Ref auto-detection)

Service usage (declarative)::

    class Solana(Service):
        SERVICE_CLS = SolanaClient
        get_slot = method(IntValue, "getSlot")

    Solana.get_slot()             # class-level access (ref factory)

Both produce the same term tree::

    IntValue(MethodCallCmd(<ref>(), "getSlot"))
    → at execution: ref.fetch(ctx) → ctx.get(SolanaClient) → client
    → client.getSlot() → result
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.abc.method import method
from everybase.core import Model, Ref


if TYPE_CHECKING:
    from everybase.core import Context


__all__ = [
    "Service",
    "ServiceRef",
]


# =============================================================================
# ServiceRef — ref term (lives in expression trees)
# =============================================================================


class ServiceRef[ServiceT](Model, Ref[ServiceT]):
    """Service ref — resolves a service client from context.

    Like PrimitiveRef resolves a value from a PV store,
    ServiceRef resolves a service client from context.

    Subclass directly with method() descriptors for imperative usage,
    or use Service for declarative class-level access.

    SERVICE_CLS: service client class, used as the context key.
    """

    SERVICE_CLS: type[ServiceT]

    def __init__(self) -> None:
        super().__init__()

    async def resolve(self, ctx: Context) -> tuple[type, ...]:
        """Identity: the service ref type itself."""
        return (type(self),)

    async def fetch(self, ctx: Context) -> ServiceT:
        """Resolve service client from context."""
        return ctx.get(self.SERVICE_CLS)


# =============================================================================
# Service — declarative entry point (like Shape for ShapeRef)
# =============================================================================


class Service:
    """Declarative entry point for services.

    Like Shape is the declarative entry point for ShapeRef,
    Service is the declarative entry point for ServiceRef.

    Subclass per service. Declare methods with ``method()`` descriptors.
    Set ``SERVICE_CLS`` to the service client class.

    ``__init_subclass__`` creates a concrete ServiceRef subclass
    and wires each method descriptor with it as ref factory.
    The generated ref class is stored as ``_ref_cls``.

    Usage::

        class Solana(Service):
            SERVICE_CLS = SolanaClient
            get_slot = method(IntValue, "getSlot")

        slot = await Solana.get_slot().execute(ctx)
    """

    SERVICE_CLS: type
    _ref_cls: type[ServiceRef]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        service_cls = cls.__dict__.get("SERVICE_CLS")
        if service_cls is None:
            return

        # Create a concrete ServiceRef subclass for this service
        ref_cls: type[ServiceRef] = type(
            f"_{cls.__name__}Ref",
            (ServiceRef,),
            {"SERVICE_CLS": service_cls},
        )
        cls._ref_cls = ref_cls

        # Wire each method descriptor with the ref factory
        for attr in cls.__dict__.values():
            if isinstance(attr, method):
                attr.bind_ref_factory(ref_cls)
