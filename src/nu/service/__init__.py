"""Nu Service fabric: expose Python objects as Nu Services.

Surface:
    - ServiceFabric: holds one Python target instance, bound via Provide.
    - QueryRef / StreamQueryRef / ActionRef / StreamActionRef / CommandRef:
      MethodRefs, one per canonical Nu kind (scalar / stream x read / mutate,
      plus void Command).
    - ServiceQuery / ServiceStreamQuery / ServiceAction / ServiceStreamAction /
      ServiceCommand: the interactions produced when the matching Ref is called.
    - bind(service_cls, target=...): Provide the ServiceFabric tagged by
      the Service class.

Example::

    class Calculator:
        def __init__(self): self.total = 0
        def add(self, a, b): return a + b
        def bump(self, by): self.total += by; return self.total
        def reset(self): self.total = 0

    class Calc(nu.Service):
        add   = nu.service.QueryRef.method()
        bump  = nu.service.ActionRef.method()
        reset = nu.service.CommandRef.method()

    app = nu.With(
        nu.service.bind(Calc, target=Calculator()),
        body=nu.print(Calc.add(a=1, b=2)),
    )
"""

from __future__ import annotations

from .fabric import ServiceFabric
from .interactions import (
    ServiceAction,
    ServiceCommand,
    ServiceQuery,
    ServiceStreamAction,
    ServiceStreamQuery,
)
from .presets import bind
from .refs import ActionRef, CommandRef, QueryRef, StreamActionRef, StreamQueryRef


__all__ = [
    "ActionRef",
    "CommandRef",
    "QueryRef",
    "ServiceAction",
    "ServiceCommand",
    "ServiceFabric",
    "ServiceQuery",
    "ServiceStreamAction",
    "ServiceStreamQuery",
    "StreamActionRef",
    "StreamQueryRef",
    "bind",
]
