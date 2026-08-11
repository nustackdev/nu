"""Nu HTTP fabric: HttpFabric + HttpMethodRef + 5 verb interactions + factories."""

from __future__ import annotations

from .fabric import HttpFabric
from .interactions import HttpDelete, HttpGet, HttpPatch, HttpPost, HttpPut
from .methods import DELETE, GET, PATCH, POST, PUT
from .presets import bind
from .refs import HttpMethodRef


__all__ = [
    "DELETE",
    "GET",
    "PATCH",
    "POST",
    "PUT",
    "HttpDelete",
    "HttpFabric",
    "HttpGet",
    "HttpMethodRef",
    "HttpPatch",
    "HttpPost",
    "HttpPut",
    "bind",
]
