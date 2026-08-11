"""5 Service interactions, one per canonical Nu kind.

ServiceQuery         (ScalarQuery)   — pure scalar read.
ServiceStreamQuery   (StreamQuery)   — pure stream read.
ServiceAction        (ScalarAction)  — mutating scalar call, yields a value.
ServiceStreamAction  (StreamAction)  — mutating stream call, yields items.
ServiceCommand       (Command)       — mutating void call, yields nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarAction, ScalarQuery, StreamAction, StreamQuery

from .core import (
    acompile_scalar,
    acompile_stream,
    acompile_void,
    compile_scalar,
    compile_stream,
    compile_void,
)


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "ServiceAction",
    "ServiceCommand",
    "ServiceQuery",
    "ServiceStreamAction",
    "ServiceStreamQuery",
]


class ServiceQuery(ScalarQuery):
    """Read-only scalar call: yields the method's return value."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_scalar(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_scalar(children)


class ServiceStreamQuery(StreamQuery):
    """Read-only stream call: yields items from the returned iterable."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_stream(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_stream(children)


class ServiceAction(ScalarAction):
    """Mutating scalar call: yields the method's return value, marks endpoint WRITE."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_scalar(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_scalar(children)


class ServiceStreamAction(StreamAction):
    """Mutating stream call: yields items, marks endpoint WRITE."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_stream(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_stream(children)


class ServiceCommand(Command):
    """Mutating void call: yields nothing, marks endpoint WRITE."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_void(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_void(children)
