"""Bindings: how a parent hands values to its body through mem.

A :class:`Binding` names a Shape and the slots the handed values go to. Per
body execution, ``push`` builds a fresh dict holding the values, binds it
under the Shape in a new frame on top of the parent's Context, and the body
runs on that Context. The body reads the values through the Shape's refs.

The rule: interaction code never mutates a store a reader can already see.
Every body execution gets its own disposable frame, pushed from the same
parent Context, so work detached from it (a delayed task, a debounced run, a
stream pulled later) reads the values of the execution that started it::

    for elem in items:
        body(rt.on(binding.push(rt.ctx, elem)))

Nothing is restored on exit: the frame is dropped with the body, and a task
still holding the body's Runtime keeps it alive.

Built once, at construction:

- ``Binding.of(Shape, slots)``: a Shape declared by the user (``let(Tally, ...)``).
- ``Binding.of_lambda(owner, fn, handed)``: a Shape generated from the body
  lambda, one slot per parameter, cached per code object. The lambda is
  called once with the slots' refs and returns the body tree.
- ``Binding.of_named(owner, fn, values)``: the same, the values given by
  parameter name (``let`` and the Teleports).
- ``Binding.none()``: a body that reads nothing; ``push`` hands ``ctx`` back.

An interaction with several bodies that each read what it hands (``Retry``'s
hooks, ``ReactWhile``'s condition and body) keeps one Binding per body.

Free form arity, one rule for every lambda binding: the lambda may take fewer
parameters than the values handed and gets the leading ones, in order; more
parameters than values fails at build. A body given as a plain tree, not a
lambda, is a lambda taking none: it reads nothing it is handed, and its
binding pushes no frame.

Lives in ``nu.lang`` rather than ``nu.mem`` so the core interactions can use
it while ``nu.mem`` is still loading; the Shape machinery it stands on is
imported when a Shape is first generated.
"""

from __future__ import annotations

import inspect
import types
from functools import cache
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from nu.domains.shape import Shape
    from nu.lang.runtime import Context


__all__ = ["Binding", "is_builder", "lambda_params"]


_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
_VARIADIC = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


class Binding:
    """One binding: the Shape a body reads and the slots the handed values go to.

    Immutable and built once, at construction. At run time ``push`` gives
    each body execution a frame of its own holding the values.

    A binding with no Shape (:meth:`none`, a body that reads nothing) pushes
    no frame: ``push`` hands ``ctx`` back as it is.
    """

    __slots__ = ("shape", "slots")

    shape: type[Shape] | None
    slots: tuple[str, ...]

    def __init__(self, shape: type[Shape] | None, slots: Sequence[str] = ()) -> None:
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "slots", tuple(slots))

    @classmethod
    def none(cls) -> Binding:
        """The binding of a body that reads nothing: a plain tree, or a lambda taking no parameter."""
        return _NONE

    @classmethod
    def of(cls, shape: type[Shape], slots: Sequence[str] | None = None) -> Binding:
        """A binding over the declared ``shape``, the values handed going to ``slots`` in order.

        ``slots`` defaults to every slot of ``shape``, in declaration order.
        """
        return cls(shape, tuple(shape._slots) if slots is None else slots)

    @classmethod
    def of_lambda(cls, owner: str, fn: object, handed: int) -> tuple[object, Binding]:
        """The body ``fn`` builds and its binding over the Shape generated from it. Build time.

        Args:
            owner: the interaction's name, for error messages.
            fn: the body, a lambda taking one parameter per value it reads, or a
                plain tree that reads none (passed through as the body).
            handed: how many values the interaction hands, in order.

        Raises:
            TypeError: ``fn`` takes more parameters than ``handed`` or a variable
                list of them, or returns None.
        """
        if not is_builder(fn):
            return fn, _NONE
        params = lambda_params(owner, fn)
        if len(params) > handed:
            what = "value" if handed == 1 else "values"
            msg = (
                f"{owner} hands its body {handed} {what}, so its lambda takes at most "
                f"{handed}; got {_spelled(fn)}"
            )
            raise TypeError(msg)
        if params:
            shape, slots = _generated(fn.__code__, params)  # type: ignore[attr-defined]
            binding = cls(shape, slots)
            refs = [getattr(shape, s) for s in slots]
        else:
            binding, refs = _NONE, []
        body = fn(*refs)  # type: ignore[operator]
        if body is None:
            msg = f"{owner}: the lambda returned None, it must return the body tree"
            raise TypeError(msg)
        return body, binding

    @classmethod
    def of_named(
        cls, owner: str, fn: object, values: Mapping[str, object]
    ) -> tuple[object, Binding, tuple]:
        """The body ``fn`` builds, its binding, and ``values`` in slot order. Build time.

        The values are given by parameter name, the rule ``let`` and the
        Teleports share: every parameter takes a value and every value names a
        parameter. A plain tree (not a lambda) takes no values and binds nothing.

        Raises:
            TypeError: a parameter has no value, a value names no parameter, a
                tree is given values, or ``fn`` breaks :meth:`of_lambda`'s rules.
        """
        if not is_builder(fn):
            if values:
                msg = (
                    f"{owner}: a tree body takes no values; got {list(values)}, "
                    "pass a lambda over them"
                )
                raise TypeError(msg)
            return fn, _NONE, ()
        params = lambda_params(owner, fn)
        missing = [p for p in params if p not in values]
        unknown = [k for k in values if k not in params]
        if missing or unknown:
            parts = []
            if missing:
                parts.append(f"no value for {missing}")
            if unknown:
                parts.append(f"{unknown} name no parameter")
            msg = f"{owner}: the lambda's parameters are {list(params)}; {', '.join(parts)}"
            raise TypeError(msg)
        body, binding = cls.of_lambda(owner, fn, len(params))
        return body, binding, tuple(values[p] for p in params)

    def push(self, ctx: Context, /, *values: object, **named: object) -> Context:
        """``ctx`` with a new frame holding ``values`` under the Shape. Run time, per body execution.

        Positional values fill the leading slots in order; more values than
        slots hand only the leading ones (the lambda took fewer), fewer leave
        the rest unset. Named values go to the slot of that name. The dict is
        built in full before it is bound and never written after.

        Raises:
            TypeError: a named value names no slot of the Shape.
        """
        shape = self.shape
        if shape is None:
            return ctx
        lowers = _lowers(shape)
        data = {name: lowers[name](v) for name, v in zip(self.slots, values, strict=False)}
        for name, v in named.items():
            lower = lowers.get(name)
            if lower is None:
                msg = f"{shape.__name__} has no slot {name!r}"
                raise TypeError(msg)
            data[name] = lower(v)
        return ctx.bind(dict, data, shape)

    def __setattr__(self, name: str, value: object) -> None:
        msg = "a Binding is immutable"
        raise AttributeError(msg)

    def __reduce__(self) -> tuple:
        return (Binding, (self.shape, self.slots))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Binding):
            return NotImplemented
        return self.shape is other.shape and self.slots == other.slots

    def __hash__(self) -> int:
        return hash((self.shape, self.slots))

    def __repr__(self) -> str:
        if self.shape is None:
            return "Binding()"
        return f"Binding({self.shape.__name__}, {list(self.slots)})"


_NONE = Binding(None)


def is_builder(slot: object) -> bool:
    """Whether ``slot`` is a function that builds a body rather than the body itself."""
    return isinstance(slot, (types.FunctionType, types.MethodType))


def lambda_params(owner: str, fn: object) -> tuple[str, ...]:
    """The positional parameter names of the body lambda ``fn``.

    Raises:
        TypeError: ``fn`` is not a function, or takes ``*args``, ``**kwargs``
            or a keyword-only parameter without a default.
    """
    if not is_builder(fn):
        msg = f"{owner} needs a function to build its body, got {type(fn).__name__}"
        raise TypeError(msg)
    names: list[str] = []
    for p in inspect.signature(fn).parameters.values():  # type: ignore[arg-type]
        if p.kind in _POSITIONAL:
            names.append(p.name)
        elif p.kind in _VARIADIC or p.default is inspect.Parameter.empty:
            msg = f"{owner}: its lambda takes a fixed list of positional parameters; got {_spelled(fn)}"
            raise TypeError(msg)
    return tuple(names)


def _spelled(fn: object) -> str:
    """``fn`` as name and signature, for an error message."""
    return f"{getattr(fn, '__name__', fn)}{inspect.signature(fn)}"  # type: ignore[arg-type]


@cache
def _generated(
    code: types.CodeType, params: tuple[str, ...]
) -> tuple[type[Shape], tuple[str, ...]]:
    """The Shape bindings built by ``code`` bind, the same class every time, and its slots.

    One ``ObjectRef`` slot per parameter, named after it; a name that would
    clash with a ref method (a slot is reached as an attribute of its ref)
    gets a trailing underscore. Each lambda gets its own Shape, so bindings
    nested in each other never share one, and building the same source twice
    gives the same Shapes and equal trees.
    """
    from nu.domains.shape import Shape
    from nu.domains.shape.dsl import _public_names, _shape_ref_classes
    from nu.mem.refs import ObjectRef

    reserved = set().union(*(_public_names(c) for c in _shape_ref_classes()))
    slots: list[str] = []
    for p in params:
        name = p
        while name in reserved or name in slots:
            name += "_"
        slots.append(name)

    def body(ns: dict[str, object]) -> None:
        for name in slots:
            ns[name] = ObjectRef.slot()
        ns["__module__"] = __name__

    return types.new_class(f"Let_{code.co_firstlineno}", (Shape,), exec_body=body), tuple(slots)


@cache
def _lowers(shape: type[Shape]) -> dict[str, Callable[[object], object]]:
    """Per slot of ``shape``, how a value is put in storage form (the slot ref's ``_lower``)."""
    return {name: getattr(shape, name)._lower for name in shape._slots}
