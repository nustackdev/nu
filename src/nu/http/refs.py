"""HTTP MethodRefs: one Ref class per verb, declaration-style.

Each verb Ref inlines `.method(...)` and `__call__` directly. Repetition
is intentional: this is a declarative surface, and inlining keeps every
verb readable end-to-end without hopping to a base class.

`.method(...)` is annotated as returning the Ref subclass itself
(`-> POSTRef`, `-> GETRef`, ...). That is a deliberate lie: at runtime it
returns a `Method` declaration which the ServiceMeta descriptor unwraps at
class access. The lie makes `Solana.get_slot` resolve to `POSTRef` in a
type checker, so `Solana.get_slot(...)` type-checks as `POSTRef.__call__`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import HttpDelete, HttpGet, HttpPatch, HttpPost, HttpPut


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["DELETERef", "GETRef", "PATCHRef", "POSTRef", "PUTRef"]


class GETRef(MethodRef):
    """A GET endpoint, declared once on a Service and called wherever it is needed.

    The declaration carries the path and any default query parameters; the
    call carries the rest. Reading the name back off the Service class hands
    out a fresh Ref that knows which Service owns it, and that Service is the
    tag the HttpFabric is resolved under, so two Services can declare the
    same verb against different base URLs.

    Notes:
        - Only meaningful in a ``Service`` class body: ``.method(...)`` yields
          a declaration, and the Service metaclass turns it into the
          descriptor that hands out the Ref.
        - ``{name}`` placeholders in the path are filled from the call
          kwargs, and those kwargs are consumed rather than also sent.
        - Whatever kwargs are left ride as query parameters, layered over the
          declared defaults, so a call can override a default but a default
          can never fill a path placeholder.
        - Calling the Ref builds an ``HttpGet`` and sends nothing; the request
          goes out when the tree runs.

    Example:
        class GH(nu.Service):
            get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")
        app = nu.With(
            nu.http.bind(GH, base_url="https://api.github.com"),
            body=GH.get_repo(owner="nu", name="core"),
        )
    """

    @classmethod
    def method(cls, path: str, **defaults: object) -> GETRef:  # type: ignore[override]
        """Declare a GET endpoint, for assignment in a Service class body.

        Args:
            path: the endpoint path, joined onto the fabric's base_url. Any
                ``{name}`` in it is filled from the call kwargs.
            **defaults: query parameters sent on every call, each overridable
                by a call kwarg of the same name.

        Notes:
            - The annotation is a deliberate lie. This returns a ``Method``
              declaration; the Service descriptor is what turns class access
              into the ``GETRef`` the annotation promises.

        Yields:
            A ``Method`` declaration, which reads back off the Service class
            as a fresh ``GETRef``.
        """
        return Method(cls, verb="GET", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the GET interaction for one call of this endpoint.

        Args:
            **kwargs: values for the path placeholders, plus the query
                parameters for this call.

        Yields:
            An ``HttpGet`` over this Ref and the kwargs. Nothing is sent
            until the tree runs.
        """
        return HttpGet(self, Dict.of(**kwargs))


class POSTRef(MethodRef):
    """A POST endpoint, declared once on a Service and called wherever it is needed.

    The declaration carries the path and any default body fields; the call
    carries the rest. Reading the name back off the Service class hands out a
    fresh Ref that knows which Service owns it, and that Service is the tag
    the HttpFabric is resolved under, so two Services can declare the same
    verb against different base URLs.

    Notes:
        - Only meaningful in a ``Service`` class body: ``.method(...)`` yields
          a declaration, and the Service metaclass turns it into the
          descriptor that hands out the Ref.
        - ``{name}`` placeholders in the path are filled from the call
          kwargs, and those kwargs are consumed rather than also sent.
        - Whatever kwargs are left ride as the JSON body, layered over the
          declared defaults, so a call can override a default but a default
          can never fill a path placeholder.
        - Calling the Ref builds an ``HttpPost`` and sends nothing; the
          request goes out when the tree runs.

    Example:
        class GH(nu.Service):
            create_issue = nu.http.POSTRef.method("/repos/{owner}/{name}/issues")
        app = nu.With(
            nu.http.bind(GH, base_url="https://api.github.com"),
            body=GH.create_issue(owner="nu", name="core", title="bug"),
        )
    """

    @classmethod
    def method(cls, path: str, **defaults: object) -> POSTRef:  # type: ignore[override]
        """Declare a POST endpoint, for assignment in a Service class body.

        Args:
            path: the endpoint path, joined onto the fabric's base_url. Any
                ``{name}`` in it is filled from the call kwargs.
            **defaults: body fields sent on every call, each overridable by a
                call kwarg of the same name.

        Notes:
            - The annotation is a deliberate lie. This returns a ``Method``
              declaration; the Service descriptor is what turns class access
              into the ``POSTRef`` the annotation promises.

        Yields:
            A ``Method`` declaration, which reads back off the Service class
            as a fresh ``POSTRef``.
        """
        return Method(cls, verb="POST", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the POST interaction for one call of this endpoint.

        Args:
            **kwargs: values for the path placeholders, plus the JSON body
                fields for this call.

        Yields:
            An ``HttpPost`` over this Ref and the kwargs. Nothing is sent
            until the tree runs.
        """
        return HttpPost(self, Dict.of(**kwargs))


class PUTRef(MethodRef):
    """A PUT endpoint, declared once on a Service and called wherever it is needed.

    The declaration carries the path and any default body fields; the call
    carries the rest. Reading the name back off the Service class hands out a
    fresh Ref that knows which Service owns it, and that Service is the tag
    the HttpFabric is resolved under, so two Services can declare the same
    verb against different base URLs.

    Notes:
        - Only meaningful in a ``Service`` class body: ``.method(...)`` yields
          a declaration, and the Service metaclass turns it into the
          descriptor that hands out the Ref.
        - ``{name}`` placeholders in the path are filled from the call
          kwargs, and those kwargs are consumed rather than also sent.
        - Whatever kwargs are left ride as the JSON body, layered over the
          declared defaults, so a call can override a default but a default
          can never fill a path placeholder.
        - Calling the Ref builds an ``HttpPut`` and sends nothing; the request
          goes out when the tree runs.

    Example:
        class Store(nu.Service):
            put_item = nu.http.PUTRef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.put_item(id=7, name="anvil"),
        )
    """

    @classmethod
    def method(cls, path: str, **defaults: object) -> PUTRef:  # type: ignore[override]
        """Declare a PUT endpoint, for assignment in a Service class body.

        Args:
            path: the endpoint path, joined onto the fabric's base_url. Any
                ``{name}`` in it is filled from the call kwargs.
            **defaults: body fields sent on every call, each overridable by a
                call kwarg of the same name.

        Notes:
            - The annotation is a deliberate lie. This returns a ``Method``
              declaration; the Service descriptor is what turns class access
              into the ``PUTRef`` the annotation promises.

        Yields:
            A ``Method`` declaration, which reads back off the Service class
            as a fresh ``PUTRef``.
        """
        return Method(cls, verb="PUT", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the PUT interaction for one call of this endpoint.

        Args:
            **kwargs: values for the path placeholders, plus the JSON body
                fields for this call.

        Yields:
            An ``HttpPut`` over this Ref and the kwargs. Nothing is sent
            until the tree runs.
        """
        return HttpPut(self, Dict.of(**kwargs))


class PATCHRef(MethodRef):
    """A PATCH endpoint, declared once on a Service and called wherever it is needed.

    The declaration carries the path and any default body fields; the call
    carries the rest. Reading the name back off the Service class hands out a
    fresh Ref that knows which Service owns it, and that Service is the tag
    the HttpFabric is resolved under, so two Services can declare the same
    verb against different base URLs.

    Notes:
        - Only meaningful in a ``Service`` class body: ``.method(...)`` yields
          a declaration, and the Service metaclass turns it into the
          descriptor that hands out the Ref.
        - ``{name}`` placeholders in the path are filled from the call
          kwargs, and those kwargs are consumed rather than also sent.
        - Whatever kwargs are left ride as the JSON body, layered over the
          declared defaults, so a call can override a default but a default
          can never fill a path placeholder.
        - Calling the Ref builds an ``HttpPatch`` and sends nothing; the
          request goes out when the tree runs.

    Example:
        class Store(nu.Service):
            patch_item = nu.http.PATCHRef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.patch_item(id=7, name="anvil"),
        )
    """

    @classmethod
    def method(cls, path: str, **defaults: object) -> PATCHRef:  # type: ignore[override]
        """Declare a PATCH endpoint, for assignment in a Service class body.

        Args:
            path: the endpoint path, joined onto the fabric's base_url. Any
                ``{name}`` in it is filled from the call kwargs.
            **defaults: body fields sent on every call, each overridable by a
                call kwarg of the same name.

        Notes:
            - The annotation is a deliberate lie. This returns a ``Method``
              declaration; the Service descriptor is what turns class access
              into the ``PATCHRef`` the annotation promises.

        Yields:
            A ``Method`` declaration, which reads back off the Service class
            as a fresh ``PATCHRef``.
        """
        return Method(cls, verb="PATCH", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the PATCH interaction for one call of this endpoint.

        Args:
            **kwargs: values for the path placeholders, plus the JSON body
                fields for this call.

        Yields:
            An ``HttpPatch`` over this Ref and the kwargs. Nothing is sent
            until the tree runs.
        """
        return HttpPatch(self, Dict.of(**kwargs))


class DELETERef(MethodRef):
    """A DELETE endpoint, declared once on a Service and called wherever it is needed.

    The declaration carries the path and any default query parameters; the
    call carries the rest. Reading the name back off the Service class hands
    out a fresh Ref that knows which Service owns it, and that Service is the
    tag the HttpFabric is resolved under, so two Services can declare the
    same verb against different base URLs.

    Notes:
        - Only meaningful in a ``Service`` class body: ``.method(...)`` yields
          a declaration, and the Service metaclass turns it into the
          descriptor that hands out the Ref.
        - ``{name}`` placeholders in the path are filled from the call
          kwargs, and those kwargs are consumed rather than also sent.
        - Whatever kwargs are left ride as query parameters, not a body,
          layered over the declared defaults.
        - Calling the Ref builds an ``HttpDelete`` and sends nothing; the
          request goes out when the tree runs.

    Example:
        class Store(nu.Service):
            delete_item = nu.http.DELETERef.method("/items/{id}")
        app = nu.With(
            nu.http.bind(Store, base_url="https://api.example.com"),
            body=Store.delete_item(id=7),
        )
    """

    @classmethod
    def method(cls, path: str, **defaults: object) -> DELETERef:  # type: ignore[override]
        """Declare a DELETE endpoint, for assignment in a Service class body.

        Args:
            path: the endpoint path, joined onto the fabric's base_url. Any
                ``{name}`` in it is filled from the call kwargs.
            **defaults: query parameters sent on every call, each overridable
                by a call kwarg of the same name.

        Notes:
            - The annotation is a deliberate lie. This returns a ``Method``
              declaration; the Service descriptor is what turns class access
              into the ``DELETERef`` the annotation promises.

        Yields:
            A ``Method`` declaration, which reads back off the Service class
            as a fresh ``DELETERef``.
        """
        return Method(cls, verb="DELETE", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build the DELETE interaction for one call of this endpoint.

        Args:
            **kwargs: values for the path placeholders, plus the query
                parameters for this call.

        Yields:
            An ``HttpDelete`` over this Ref and the kwargs. Nothing is sent
            until the tree runs.
        """
        return HttpDelete(self, Dict.of(**kwargs))
