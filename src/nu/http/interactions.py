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
    """GET: safe read, yields parsed JSON."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPost(ScalarAction):
    """POST: creates, yields parsed JSON response."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPut(ScalarAction):
    """PUT: replaces, yields parsed JSON response."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpPatch(ScalarAction):
    """PATCH: partial update, yields parsed JSON response."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)


class HttpDelete(ScalarAction):
    """DELETE: yields parsed JSON response (empty dict on 204)."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)
