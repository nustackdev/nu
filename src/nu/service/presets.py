"""bind(): Provide an ServiceFabric wrapping a Python target for a service."""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import ServiceFabric


__all__ = ["bind"]


def bind(service_cls: type, *, target: object) -> Provide:
    """Provide an ServiceFabric tagged by the service class."""
    return Provide(ServiceFabric, {"target": target}, tag=service_cls)
