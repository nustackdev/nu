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
    """Give one Service class its HTTP transport, for the span of a tree.

    Args:
        service_cls: the Service whose endpoints this transport serves. It is
            also the tag the fabric is bound under, so one tree can carry a
            separate transport per Service.
        base_url: prefix every declared path is joined onto.
        headers: sent on every request through this fabric.
        timeout: seconds a single request may take.

    Notes:
        - Drops into a ``With`` alongside other providers; it is a bracket,
          so the clients open when the body starts and close when it ends.
        - Which client opens follows the runtime: a sync run opens the sync
          client, an async run the async one. Calling an endpoint under the
          runtime whose client never opened raises.
        - Endpoints of a Service with no matching bind cannot resolve a
          fabric, so binding is what makes a declared Service callable at all.

    Example:
        class GH(nu.Service):
            get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")
        app = nu.With(
            nu.http.bind(GH, base_url="https://api.github.com", timeout=5.0),
            body=nu.print(GH.get_repo(owner="nu", name="core")),
        )
    """
    return Provide(
        HttpFabric,
        {"base_url": base_url, "headers": headers, "timeout": timeout},
        tag=service_cls,
    )
