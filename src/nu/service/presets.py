"""bind(): Provide a ServiceFabric wrapping a Python target for a Service."""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import ServiceFabric


__all__ = ["bind"]


def bind(service_cls: type, *, target: object) -> Provide:
    """Wire a Python object as the backing target for a Service's endpoints.

    Args:
        service_cls: the ``nu.Service`` subclass whose endpoints dispatch here.
            Used as the context tag; it is never instantiated.
        target: any Python object. Each endpoint resolves to the attribute of
            the same name on it, or the name given to ``.method(name=...)``.

    Notes:
        - The tag is the Service class itself, which is also what the
          interactions look up, so several Services over several targets live
          side by side in one tree.
        - Returns the ``Provide`` bracket with no body, so it is written as the
          first argument of a ``nu.With`` and scopes to that body. Endpoints
          evaluated outside it find no fabric.
        - The fabric has no setup or teardown of its own, so nothing is opened
          or closed around the object. Its lifetime stays the caller's problem.
        - The target is captured once at bind time; there is no rebinding for
          the life of the body.

    Example:
        class Calc(nu.Service):
            add = nu.service.QueryRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(Calc.add(a=1, b=2)),
        )
    """
    return Provide(ServiceFabric, {"target": target}, tag=service_cls)
