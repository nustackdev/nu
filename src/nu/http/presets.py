"""bind(): Provide an HttpFabric for a service."""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import HttpFabric


__all__ = ["bind"]


def bind(
    service_cls: type,
    *,
    base_url: str = "",
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> Provide:
    """Provide an HttpFabric tagged by the service class."""
    return Provide(
        HttpFabric,
        {"base_url": base_url, "headers": headers, "timeout": timeout},
        tag=service_cls,
    )
