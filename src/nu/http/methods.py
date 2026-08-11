"""5 Method factories: GET, POST, PUT, PATCH, DELETE.

Each builds a Method(HttpMethodRef, verb=..., path=...) with any extra config.
"""

from __future__ import annotations

from nu.domains.service import Method

from .refs import HttpMethodRef


__all__ = ["DELETE", "GET", "PATCH", "POST", "PUT"]


def _method(verb: str, path: str, **extra: object) -> Method:
    return Method(HttpMethodRef, verb=verb, path=path, **extra)


def GET(path: str, **extra: object) -> Method:
    """Declare a GET method at `path`."""
    return _method("GET", path, **extra)


def POST(path: str, **extra: object) -> Method:
    """Declare a POST method at `path`."""
    return _method("POST", path, **extra)


def PUT(path: str, **extra: object) -> Method:
    """Declare a PUT method at `path`."""
    return _method("PUT", path, **extra)


def PATCH(path: str, **extra: object) -> Method:
    """Declare a PATCH method at `path`."""
    return _method("PATCH", path, **extra)


def DELETE(path: str, **extra: object) -> Method:
    """Declare a DELETE method at `path`."""
    return _method("DELETE", path, **extra)
