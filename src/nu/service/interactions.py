"""5 Service interactions, one per canonical Nu kind.

ServiceQuery         (ScalarQuery)   — pure scalar read.
ServiceStreamQuery   (StreamQuery)   — pure stream read.
ServiceAction        (ScalarAction)  — mutating scalar call, yields a value.
ServiceStreamAction  (StreamAction)  — mutating stream call, yields items.
ServiceCommand       (Command)       — mutating void call, yields nothing.

Each takes the same two children: the endpoint Ref and a Dict of call kwargs.
None of them is written by hand — calling the matching MethodRef builds it.
Dispatch is shared: the Ref payload names the owning Service, that class is the
tag the ``ServiceFabric`` is looked up under on the context, the target
attribute is fetched off it, and the endpoint defaults are merged under the
call kwargs. What differs across the five is the kind they declare, whether
slot 0 is marked mutated, and what happens to the return value.
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
    """Calls a read-only endpoint on the bound Python object for its value.

    Args:
        ref: the endpoint Ref. Its payload names the owning Service, the target
            attribute, and the endpoint defaults.
        args: a Dict of call kwargs, merged over those defaults.

    Notes:
        - Built by calling a ``QueryRef``, not written directly.
        - The owning Service class is the context tag, so several Services over
          several targets coexist in one tree without colliding.
        - A kwarg passed at the call site wins over the endpoint default of the
          same name.
        - Under ``nu.run`` an awaitable return raises RuntimeError pointing at
          ``nu.arun``; under ``nu.arun`` it is awaited.

    Yields:
        Whatever the target returns, passed through untouched. No sentinel
        translation happens here, so a target returning None yields None.

    Example:
        class Calc(nu.Service):
            add = nu.service.QueryRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(Calc.add(a=1, b=2)),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_scalar(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_scalar(children)


class ServiceStreamQuery(StreamQuery):
    """Calls a read-only endpoint on the bound Python object for its items.

    Args:
        ref: the endpoint Ref. Its payload names the owning Service, the target
            attribute, and the endpoint defaults.
        args: a Dict of call kwargs, merged over those defaults.

    Notes:
        - Built by calling a ``StreamQueryRef``, not written directly.
        - The target is called once; only the iteration is lazy. A generator
          function therefore runs no body until the stream is pulled, but a
          function returning a list has already built the list.
        - Under ``nu.run`` an async generator return raises RuntimeError
          pointing at ``nu.arun``.
        - Under ``nu.arun`` a plain iterable, an awaitable of an iterable, and
          an async generator are all bridged to async iteration.

    Yields:
        The items of whatever the target returned, in order, pulled one at a
        time.

    Example:
        class Calc(nu.Service):
            squares = nu.service.StreamQueryRef.method(name="range")
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(nu.Collect(Calc.squares(n=4))),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_stream(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_stream(children)


class ServiceAction(ScalarAction):
    """Calls a mutating endpoint on the bound Python object for its value.

    Args:
        ref: the endpoint Ref. Its payload names the owning Service, the target
            attribute, and the endpoint defaults.
        args: a Dict of call kwargs, merged over those defaults.

    Notes:
        - Built by calling an ``ActionRef``, not written directly.
        - Slot 0 is declared mutated, so the Ref child binds as WRITE in the
          effect walk instead of READ. That is the only difference from
          ``ServiceQuery``; dispatch is identical.
        - The write is declared, never inferred. Nothing inspects the target to
          confirm it mutates anything.

    Yields:
        Whatever the target returns, passed through untouched.

    Example:
        class Calc(nu.Service):
            bump = nu.service.ActionRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(Calc.bump(by=3)),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_scalar(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_scalar(children)


class ServiceStreamAction(StreamAction):
    """Calls a mutating endpoint on the bound Python object for its items.

    Args:
        ref: the endpoint Ref. Its payload names the owning Service, the target
            attribute, and the endpoint defaults.
        args: a Dict of call kwargs, merged over those defaults.

    Notes:
        - Built by calling a ``StreamActionRef``, not written directly.
        - Slot 0 is declared mutated, so the Ref child binds as WRITE. That is
          the only difference from ``ServiceStreamQuery``; dispatch is identical.
        - The write is attributed to the call, not to each pull, so a generator
          that only mutates while draining still reads as a write on the node.

    Yields:
        The items of whatever the target returned, in order, pulled one at a
        time.

    Example:
        class Calc(nu.Service):
            drain = nu.service.StreamActionRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=nu.print(nu.Collect(Calc.drain())),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_stream(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_stream(children)


class ServiceCommand(Command):
    """Calls a mutating endpoint on the bound Python object for effect only.

    Args:
        ref: the endpoint Ref. Its payload names the owning Service, the target
            attribute, and the endpoint defaults.
        args: a Dict of call kwargs, merged over those defaults.

    Notes:
        - Built by calling a ``CommandRef``, not written directly.
        - Slot 0 is declared mutated, so the Ref child binds as WRITE.
        - The return value is dropped after the awaitable check, so a target
          that does return something can still be wired here.
        - Under ``nu.run`` an awaitable return raises RuntimeError pointing at
          ``nu.arun``; under ``nu.arun`` it is awaited, then discarded.

    Yields:
        Nothing. Always None, whatever the target returned.

    Example:
        class Calc(nu.Service):
            reset = nu.service.CommandRef.method()
        app = nu.With(
            nu.service.bind(Calc, target=Calculator()),
            body=Calc.reset(),
        )
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_void(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_void(children)
