"""5 HTTP interactions: HttpGet, HttpPost, HttpPut, HttpPatch, HttpDelete.

GET is a ScalarQuery (safe verb, no mutation attribution).
POST / PUT / PATCH / DELETE are ScalarActions (mutate, still yield the response body).

Each class inlines its own `_mutates` (mutating verbs) + `_compile` / `_acompile`.
Shared wire logic lives in `nu.http.core`. Repetition across the 4 mutating verbs
is intentional: this is declaration-style code, read straight through.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction, ScalarQuery

from .core import acompile_call, compile_call


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "HttpDelete",
    "HttpGet",
    "HttpPatch",
    "HttpPost",
    "HttpPut",
]


class HttpGet(ScalarQuery):
    """One GET request over an endpoint declared with GETRef.

    Args:
        endpoint: the GETRef, yielding the path, the declared defaults and
            the Service that owns the endpoint.
        args: the call kwargs, as a Dict.

    Notes:
        - Written by calling a ``GETRef``, not by hand: the Ref call is what
          pairs the endpoint with its kwargs.
        - Path placeholders are filled from ``args`` and consumed; what is
          left layers over the declared defaults and rides as query
          parameters.
        - The fabric is resolved on the runtime context as an ``HttpFabric``
          tagged by the owning Service, so the request only works inside a
          ``With`` that bound one for that Service.
        - A non-2xx response raises rather than yielding a value, so an HTTP
          error is a real error and never a sentinel.
        - Safe verb: nothing is declared mutated, so the endpoint binds as a
          READ effect.

    Yields:
        The response body, parsed as JSON.

    Example:
        class GH(nu.Service):
            get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")
        app = nu.With(
            nu.http.bind(GH, base_url="https://api.github.com"),
            body=nu.print(GH.get_repo(owner="nu", name="core")),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPost(ScalarAction):
    """One POST request over an endpoint declared with POSTRef.

    Args:
        endpoint: the POSTRef, yielding the path, the declared defaults and
            the Service that owns the endpoint.
        args: the call kwargs, as a Dict.

    Notes:
        - Written by calling a ``POSTRef``, not by hand: the Ref call is what
          pairs the endpoint with its kwargs.
        - Path placeholders are filled from ``args`` and consumed; what is
          left layers over the declared defaults and is sent as the JSON
          body.
        - The fabric is resolved on the runtime context as an ``HttpFabric``
          tagged by the owning Service, so the request only works inside a
          ``With`` that bound one for that Service.
        - A non-2xx response raises rather than yielding a value, so an HTTP
          error is a real error and never a sentinel.
        - The endpoint sits in the mutation slot, so it binds as a WRITE
          effect: the request is assumed to change something on the far side.

    Yields:
        The response body, parsed as JSON.

    Example:
        class GH(nu.Service):
            create_issue = nu.http.POSTRef.method("/repos/{owner}/{name}/issues")
        app = nu.With(
            nu.http.bind(GH, base_url="https://api.github.com"),
            body=GH.create_issue(owner="nu", name="core", title="bug"),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPut(ScalarAction):
    """One PUT request over an endpoint declared with PUTRef.

    Args:
        endpoint: the PUTRef, yielding the path, the declared defaults and
            the Service that owns the endpoint.
        args: the call kwargs, as a Dict.

    Notes:
        - Written by calling a ``PUTRef``, not by hand: the Ref call is what
          pairs the endpoint with its kwargs.
        - Path placeholders are filled from ``args`` and consumed; what is
          left layers over the declared defaults and is sent as the JSON
          body.
        - The fabric is resolved on the runtime context as an ``HttpFabric``
          tagged by the owning Service, so the request only works inside a
          ``With`` that bound one for that Service.
        - A non-2xx response raises rather than yielding a value, so an HTTP
          error is a real error and never a sentinel.
        - The endpoint sits in the mutation slot, so it binds as a WRITE
          effect: the request is assumed to change something on the far side.

    Yields:
        The response body, parsed as JSON.

    Example:
        class Store(nu.Service):
            put_item = nu.http.PUTRef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.put_item(id=7, name="anvil"),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPatch(ScalarAction):
    """One PATCH request over an endpoint declared with PATCHRef.

    Args:
        endpoint: the PATCHRef, yielding the path, the declared defaults and
            the Service that owns the endpoint.
        args: the call kwargs, as a Dict.

    Notes:
        - Written by calling a ``PATCHRef``, not by hand: the Ref call is what
          pairs the endpoint with its kwargs.
        - Path placeholders are filled from ``args`` and consumed; what is
          left layers over the declared defaults and is sent as the JSON
          body.
        - The fabric is resolved on the runtime context as an ``HttpFabric``
          tagged by the owning Service, so the request only works inside a
          ``With`` that bound one for that Service.
        - A non-2xx response raises rather than yielding a value, so an HTTP
          error is a real error and never a sentinel.
        - The endpoint sits in the mutation slot, so it binds as a WRITE
          effect: the request is assumed to change something on the far side.

    Yields:
        The response body, parsed as JSON.

    Example:
        class Store(nu.Service):
            patch_item = nu.http.PATCHRef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.patch_item(id=7, name="anvil"),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpDelete(ScalarAction):
    """One DELETE request over an endpoint declared with DELETERef.

    Args:
        endpoint: the DELETERef, yielding the path, the declared defaults and
            the Service that owns the endpoint.
        args: the call kwargs, as a Dict.

    Notes:
        - Written by calling a ``DELETERef``, not by hand: the Ref call is
          what pairs the endpoint with its kwargs.
        - Path placeholders are filled from ``args`` and consumed; what is
          left layers over the declared defaults and rides as query
          parameters, not a body.
        - The fabric is resolved on the runtime context as an ``HttpFabric``
          tagged by the owning Service, so the request only works inside a
          ``With`` that bound one for that Service.
        - A non-2xx response raises rather than yielding a value, so an HTTP
          error is a real error and never a sentinel.
        - The response is parsed as JSON unconditionally, so an endpoint that
          answers with an empty body (a bare 204) raises on the parse.
        - The endpoint sits in the mutation slot, so it binds as a WRITE
          effect: the request is assumed to change something on the far side.

    Yields:
        The response body, parsed as JSON.

    Example:
        class Store(nu.Service):
            delete_item = nu.http.DELETERef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.delete_item(id=7),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)
