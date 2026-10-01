"""Binder lambdas: a body written as a function of the values it is handed.

An interaction that hands values to its body (a loop its item, a fold its
accumulator, a catch the error) binds them in ``ctx.attrs`` under names, and
the body reads them back with ``Attr(name)``. Spelled out by hand, the names
collide: two nested loops both default to ``"item"`` and the inner one hides
the outer. The lambda form takes the names out of the author's hands. The
slot that receives the values takes a function whose parameters are those
values::

    nu.ForEachDo(rows, lambda row: nu.ForEachDo(row, lambda cell: nu.print(cell)))

The interaction calls the function once with an ``Attr`` per parameter and
keeps the tree it returns as the body, bound under those names. The tree holds
no function, only what it built.

The names belong to the function's code, the lambda as written in the source,
the same way ``nu.let`` gives each lambda its own Shape. A name is the
parameter, the line and a short digest of the code (``"row@12#a3f09c"``).
The digest reads the compiled code itself (its bytecode, names and constants,
inner lambdas included), so building the same source twice gives the same
names and equal trees, and two lambdas on one line get different names: one
holding the other differs from it by that very constant. Nothing is counted
or kept while a tree is being built.

So lambdas nested in each other never share a name. One lambda nested inside
its own body does: a recursive helper building a loop inside a loop from the
same lambda binds the same name at every level, and the inner binding shadows
the outer, as calling ``nu.let`` with the same function inside its own body
does. Name the bindings explicitly (``item=``, ``key=``, ...) when each level
must stay readable.

The function runs once, at construction, and only builds the tree. What it
receives are refs, never values: build-time Python may shape the body but
never branches on or computes with what a parameter will hold. Decisions over
it are nodes of the body (``nu.If``, ``nu.Add``) and happen when it runs. The
refs carry the Object form, so wrap them for a typed surface
(``nu.Str(name).upper()``), the same rule as ``nu.let``.
"""

from __future__ import annotations

import hashlib
import inspect
import types
from functools import cache
from typing import Any


__all__ = ["bind", "is_builder"]


_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def is_builder(slot: object) -> bool:
    """Whether ``slot`` is a function that builds a body rather than the body itself."""
    return isinstance(slot, (types.FunctionType, types.MethodType))


def bind(owner: str, slot: object, **names: object) -> tuple[Any, tuple[Any, ...]]:
    """Resolves a binder slot into the body tree and the names it binds under.

    A plain tree passes through with ``names`` as given. A function is called
    once with an ``Attr`` per binding, and its tree comes back with the names
    its code owns.

    Args:
        owner: the interaction's name, for error messages.
        slot: the body, a tree or a function building it.
        names: the explicit name params of the bindings, in the order the
            function takes them, each as the caller passed it (``None`` when
            it did not).

    Notes:
        - One function always binds the same names. Used again inside its
          own body, its inner binding shadows the outer one; an explicit
          name keeps both readable.

    Returns:
        ``(body, names)``: the body tree and one name per binding, the
        function's own for a function, as given (``None`` included) for a
        tree.

    Raises:
        ValueError: a function together with an explicit name.
        TypeError: a function that does not take one parameter per binding,
            or that returns ``None``.
    """
    if not is_builder(slot):
        return slot, tuple(names.values())
    # Late: core's binders import this module while the forms ``Attr`` stands
    # on are still loading.
    from .refs import Attr

    given = [param for param, name in names.items() if name is not None]
    if given:
        listed = ", ".join(f"{param}=" for param in given)
        msg = f"{owner}: pass the body as a lambda or name its bindings with {listed}, not both"
        raise ValueError(msg)
    fn: Any = slot
    owned = tuple(_name(fn.__code__, param) for param in _params(owner, fn, tuple(names)))
    body = fn(*(Attr(name) for name in owned))
    if body is None:
        msg = f"{owner}: the lambda returned None, it must return the body tree"
        raise TypeError(msg)
    return body, owned


@cache
def _name(code: types.CodeType, param: str) -> str:
    """The name ``code`` binds ``param`` under, the same one every time."""
    return f"{param}@{code.co_firstlineno}#{_digest(code)}"


@cache
def _digest(code: types.CodeType) -> str:
    """Six hex digits of what ``code`` compiles to, equal for equal source."""
    return hashlib.blake2s(_anatomy(code).encode(), digest_size=3).hexdigest()


def _anatomy(code: types.CodeType) -> str:
    """``code`` spelled out without addresses or hash order, inner code included."""
    parts = [
        code.co_code.hex(),
        repr(code.co_names),
        repr(code.co_varnames),
        repr(code.co_freevars),
        str(code.co_firstlineno),
    ]
    parts.extend(_constant(const) for const in code.co_consts)
    return "|".join(parts)


def _constant(const: object) -> str:
    """A code constant as a stable string: inner code by anatomy, sets sorted."""
    if isinstance(const, types.CodeType):
        return f"<{_anatomy(const)}>"
    if isinstance(const, frozenset):
        return f"frozenset({sorted(_constant(c) for c in const)})"
    if isinstance(const, tuple):
        return f"({', '.join(_constant(c) for c in const)})"
    return repr(const)


def _params(owner: str, fn: Any, bindings: tuple[str, ...]) -> list[str]:  # noqa: ANN401
    """The names of ``fn``'s parameters, one per binding; raises when the count is off."""
    signature = inspect.signature(fn)
    arity = len(bindings)
    try:
        signature.bind(*range(arity))
    except TypeError:
        what = "value" if arity == 1 else "values"
        msg = (
            f"{owner} hands its body {arity} {what} ({', '.join(bindings)}), "
            f"so its lambda takes {arity}; got {fn.__name__}{signature}"
        )
        raise TypeError(msg) from None
    positional = [p.name for p in signature.parameters.values() if p.kind in _POSITIONAL]
    return [positional[i] if i < len(positional) else f"arg{i}" for i in range(arity)]
