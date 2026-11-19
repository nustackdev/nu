"""Literal: the leaf where nu meets python.

Two forms, one class:

- ``Literal(value)`` carries a raw Python value as its one field and yields
  it, pure (no effects, no children). Most non-Ref leaves in a Nu program are
  these.
- ``Literal(factory=f, **kwargs)`` builds a fresh value on every run: the
  kwargs are children (a plain value auto-wraps, a term stays a term), each
  evaluation runs them and yields ``f(**values)``. A computation, not a
  constant: effects and cardinality fold from its children like any node.

It lives in ``lang`` rather than with the atoms in ``nu.core`` because it is a
language primitive, not a mapping of a Python builtin: ``Nu.__init__`` wraps
every non-Nu child in one, so ``Add(1, 2)`` reads the same as
``Add(Literal(1), Literal(2))``. The language cannot construct a tree without
it, and every raw value that becomes a term passes through ``Literal(value)``.

Sorts: ScalarQuery (Q).

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). The plain form returns a thunk that closes over the value; the
factory form runs on ``nu.lang.call``, the mechanism the factory atoms
(``DictOf``, ``ListOf``, ``@nu.host``) share.
"""

from __future__ import annotations

import inspect
import sys
import types
import warnings
from typing import TYPE_CHECKING

from nu.engine import Term
from nu.lang.call import call_athunk, call_thunk
from nu.lang.kinds import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Literal", "MutableLiteralWarning"]


class MutableLiteralWarning(UserWarning):
    """A Literal holds an unhashable instance every run of the program shares.

    Raised for ``Literal(x)`` (or a raw ``x`` auto-wrapped as a child) when
    ``type(x).__hash__ is None``, the rule dataclasses use for "mutable":
    whatever one run does to ``x`` the next run sees. Build a fresh one per
    run with ``Literal(factory=...)``; keep a shared live object in the
    context (a fabric, ``nu.mem``).
    """


_ABSENT = object()
"""No positional value was given (``None`` is a value)."""


class Literal(ScalarQuery):
    """A Python value as a term: carried as is, or built fresh on each run.

    Args:
        value: the Python value to carry, held in the ``value`` field and
            never evaluated: numbers, strings, classes, functions, live
            objects, even a term (held as data, not run).
        factory: instead of ``value``, a callable called on every run with
            the values of ``kwargs``; the result is yielded. Held in the
            ``factory`` field, the kwarg names in ``keys``.
        **kwargs: the factory's arguments, as children. A plain value
            auto-wraps, a term (a mem or kv read, a computation) runs.

    Raises:
        TypeError: ``value`` and ``factory`` given together, kwargs without a
            factory, a ``factory`` that is not callable or is ``async def``
            (wrap it with ``nu.host``), or a plain container that holds a term
            at any depth (copying it would carry the term as data, not run it:
            build it with ``Literal(factory=dict, ...)`` / ``Dict.of(...)``).

    Notes:
        - The right way is explicit: ``Literal(factory=...)`` (or
          ``Dict.of`` / ``List.of``) for a value a run may change.
          ``Literal(factory=lambda: [...])`` for a constant, the forms to
          compute one.
        - A thin layer catches the common mistake for the native types:
          exact ``dict``, ``list``, ``set``, ``bytearray`` (and tuples or
          frozensets holding one) are copied on each evaluation, so what a
          run does to the value never reaches the program: the mutable
          default argument trap, closed. Only the nested built-in containers
          are rebuilt; live objects, terms and custom objects inside keep
          their identity. A value with nothing mutable costs nothing.
        - Any other unhashable instance (``type(x).__hash__ is None``) warns
          with ``MutableLiteralWarning``: every run shares it. Terms,
          classes, functions and modules never warn. There is no opt-out: a
          shared live object belongs in the context (fabrics, ``nu.mem``).
        - Any tree builder that gets a raw Python value where a term is
          expected wraps it in a Literal, through the same checks.

    Yields:
        ``value`` every time (a fresh copy when it holds a native mutable
        container), or ``factory(**values)``.

    Example:
        >>> nu.run(nu.Literal(42))[0]
        42
        >>> nu.run(nu.Literal(factory=dict, a=1, b=nu.Add(1, 2)))[0]
        {'a': 1, 'b': 3}
    """

    value: object
    """The carried Python value, as given (plain form)."""

    factory: Callable[..., object] | None = None
    """The callable run on each evaluation (factory form); ``None`` on the plain form."""

    keys: tuple[str, ...]
    """The factory's keyword names, one per child, in child order (factory form)."""

    def __init__(
        self,
        value: object = _ABSENT,
        /,
        *,
        factory: Callable[..., object] | None = None,
        **kwargs: object,
    ) -> None:
        if factory is None:
            if kwargs:
                names = ", ".join(kwargs)
                msg = (
                    f"Literal got keyword children ({names}) but no factory: "
                    f"build the value with Literal(factory=dict, {names}=...)"
                )
                raise TypeError(msg)
            if value is _ABSENT:
                msg = "Literal needs a value, or factory= to build one on each run"
                raise TypeError(msg)
            _check(value)
            super().__init__()
            self.value = value
            return
        if value is not _ABSENT:
            msg = (
                f"Literal takes a value or a factory, not both (got {value!r} and "
                f"factory={factory!r}): pass the factory its inputs by keyword, "
                f"or close over a constant, Literal(factory=lambda: ...)"
            )
            raise TypeError(msg)
        if not callable(factory):
            msg = f"Literal factory must be callable, got {factory!r}"
            raise TypeError(msg)
        if inspect.iscoroutinefunction(factory) or inspect.isasyncgenfunction(factory):
            msg = (
                f"Literal factory must be a plain function, got async {factory!r}: "
                f"make it an atom with nu.host"
            )
            raise TypeError(msg)
        super().__init__(*kwargs.values())
        self.factory = factory
        self.keys = tuple(kwargs)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if self.factory is not None:
            return call_thunk(self.factory, (), self.keys, children)

        value = self.value

        if _holds_mutable(value):

            def fresh_thunk(rt: Runtime) -> object:
                return _fresh(value)

            return fresh_thunk

        def thunk(rt: Runtime) -> object:
            return value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if self.factory is not None:
            return call_athunk(self.factory, (), self.keys, children)

        value = self.value

        if _holds_mutable(value):

            async def fresh_athunk(rt: Runtime) -> object:
                return _fresh(value)

            return fresh_athunk

        async def athunk(rt: Runtime) -> object:
            return value

        return athunk


# -- the checks on a plain value ---------------------------------------------


_MUTABLE = (dict, list, set, bytearray)
"""Native mutable containers a Literal copies on evaluation (exact types only)."""

_CONTAINERS = (dict, list, tuple, set, frozenset)
"""Native containers walked for a term inside (exact types only)."""

_NEVER_WARN = (
    Term,
    type,
    types.FunctionType,
    types.BuiltinFunctionType,
    types.MethodType,
    types.ModuleType,
)
"""What a Literal carries as is without a warning, whatever its hash."""


def _check(value: object) -> None:
    """Refuse a native container holding a term; warn on an unhashable instance."""
    t = type(value)
    if t in _CONTAINERS:
        if _holds_term(value):
            msg = (
                f"Literal got a {t.__name__} holding a Nu term, which it would carry "
                f"as data, not run: build the {t.__name__} in the program with "
                f"Literal(factory={t.__name__}, ...) / nu.Dict.of(...) / nu.List.of(...), "
                f"or quote the term itself with Literal(term)"
            )
            raise TypeError(msg)
        return
    if t in _MUTABLE or t.__hash__ is not None or isinstance(value, _NEVER_WARN):
        return
    msg = (
        f"Literal holds a mutable {t.__name__} that every run shares: build it per "
        f"run with Literal(factory={t.__name__}, ...), or keep a shared live object "
        f"in the context (a fabric, nu.mem)"
    )
    warnings.warn(msg, MutableLiteralWarning, stacklevel=_caller_level())


def _holds_term(value: object) -> bool:
    """Whether a native container holds a Nu term at any depth (keys included)."""
    t = type(value)
    if t is dict:
        return any(_holds_term(k) or _holds_term(v) for k, v in value.items())  # type: ignore[attr-defined]
    if t in _CONTAINERS:
        return any(_holds_term(v) for v in value)  # type: ignore[attr-defined]
    return isinstance(value, Term)


def _caller_level() -> int:
    """The ``stacklevel`` of the first frame outside nu and nustd: the user's call."""
    frame = sys._getframe(1)
    level = 1
    while frame is not None:
        name = frame.f_globals.get("__name__", "")
        if not (name in ("nu", "nustd") or name.startswith(("nu.", "nustd."))):
            break
        frame = frame.f_back  # type: ignore[assignment]
        level += 1
    return level


def _holds_mutable(value: object) -> bool:
    """Whether ``value`` is, or holds inside tuples / frozensets, a native mutable container."""
    t = type(value)
    if t in _MUTABLE:
        return True
    if t is tuple or t is frozenset:
        return any(_holds_mutable(v) for v in value)  # type: ignore[attr-defined]
    return False


def _fresh(value: object) -> object:
    """A copy of ``value``'s native mutable containers, nested; anything else as is."""
    t = type(value)
    if t is dict:
        return {k: _fresh(v) for k, v in value.items()}  # type: ignore[attr-defined]
    if t is list:
        return [_fresh(v) for v in value]  # type: ignore[attr-defined]
    if t is set:
        return set(value)  # type: ignore[call-overload]
    if t is bytearray:
        return bytearray(value)  # type: ignore[arg-type]
    if t is tuple and _holds_mutable(value):
        return tuple(_fresh(v) for v in value)  # type: ignore[attr-defined]
    return value
