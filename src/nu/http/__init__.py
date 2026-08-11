"""Nu HTTP fabric.

Surface:
    - HttpFabric: httpx client holder (sync + async), managed by Nu's ctx.
    - GETRef / POSTRef / PUTRef / PATCHRef / DELETERef: verb MethodRefs.
      Each exposes `.method(path, **defaults)` to declare an endpoint on a Service.
    - HttpGet / HttpPost / HttpPut / HttpPatch / HttpDelete: the 5 interactions
      produced when a MethodRef is called with kwargs.
    - bind(service_cls, base_url=..., headers=..., timeout=...): Provide the
      HttpFabric tagged by the Service class.

Example::

    class GH(nu.Service):
        get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")

    app = nu.With(
        nu.http.bind(GH, base_url="https://api.github.com"),
        body=nu.print(GH.get_repo(owner="nu", name="core")),
    )
"""

from __future__ import annotations

from .fabric import HttpFabric
from .interactions import HttpDelete, HttpGet, HttpPatch, HttpPost, HttpPut
from .presets import bind
from .refs import DELETERef, GETRef, PATCHRef, POSTRef, PUTRef


__all__ = [
    "DELETERef",
    "GETRef",
    "HttpDelete",
    "HttpFabric",
    "HttpGet",
    "HttpPatch",
    "HttpPost",
    "HttpPut",
    "PATCHRef",
    "POSTRef",
    "PUTRef",
    "bind",
]
