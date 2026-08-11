"""5 HTTP interactions: HttpGet, HttpPost, HttpPut, HttpPatch, HttpDelete.

GET is a ScalarQuery (safe verb, no mutation attribution).
POST / PUT / PATCH / DELETE are ScalarActions (mutate, still yield the response body).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction, ScalarQuery

from .fabric import HttpFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "HttpDelete",
    "HttpGet",
    "HttpPatch",
    "HttpPost",
    "HttpPut",
    "verb_to_cls",
]


def _format_path(path: str, kwargs: dict) -> tuple[str, dict]:
    """Substitute {name} placeholders from kwargs; return (path, remaining kwargs)."""
    remaining = dict(kwargs)
    formatted = path
    for key in list(remaining):
        placeholder = "{" + key + "}"
        if placeholder in formatted:
            formatted = formatted.replace(placeholder, str(remaining.pop(key)))
    return formatted, remaining


def _split_kwargs(verb: str, path: str, kwargs: dict) -> tuple[str, dict]:
    """Format path, then route remaining kwargs to params (GET/DELETE) or json body."""
    formatted, remaining = _format_path(path, kwargs)
    if verb in ("GET", "DELETE"):
        return formatted, {"params": remaining}
    return formatted, {"json": remaining}


class _HttpCall:
    """Shared compile logic for the 5 verbs. children = (endpoint_ref, args_literal)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk, args_thunk = children

        def thunk(rt: Runtime) -> object:
            payload = ref_thunk(rt)
            args = args_thunk(rt)
            verb = payload["verb"]
            path, wire = _split_kwargs(verb, payload["path"], args)
            fabric = rt.ctx.get(HttpFabric, payload["owner_service"])
            return fabric.request(verb, path, **wire)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk, args_thunk = children

        async def athunk(rt: Runtime) -> object:
            payload = await ref_thunk(rt)
            args = await args_thunk(rt)
            verb = payload["verb"]
            path, wire = _split_kwargs(verb, payload["path"], args)
            fabric = rt.ctx.get(HttpFabric, payload["owner_service"])
            return await fabric.arequest(verb, path, **wire)

        return athunk


class HttpGet(_HttpCall, ScalarQuery):
    """GET: safe read, yields parsed JSON."""


class _HttpMutation(_HttpCall, ScalarAction):
    """Mutating verbs share slot-0 (endpoint ref) as the mutation attribution."""

    _mutates = Declared(value=frozenset({0}), name="mutates")


class HttpPost(_HttpMutation):
    """POST: creates, yields parsed JSON response."""


class HttpPut(_HttpMutation):
    """PUT: replaces, yields parsed JSON response."""


class HttpPatch(_HttpMutation):
    """PATCH: partial update, yields parsed JSON response."""


class HttpDelete(_HttpMutation):
    """DELETE: yields parsed JSON response (empty dict on 204)."""


_VERBS = {
    "GET": HttpGet,
    "POST": HttpPost,
    "PUT": HttpPut,
    "PATCH": HttpPatch,
    "DELETE": HttpDelete,
}


def verb_to_cls(verb: str) -> type:
    """Pick the interaction class for an HTTP verb."""
    try:
        return _VERBS[verb]
    except KeyError as e:
        msg = f"unknown HTTP verb {verb!r}; expected one of {sorted(_VERBS)}"
        raise ValueError(msg) from e
