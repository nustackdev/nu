"""Static and dynamic binding: how a parent hands values to its body through mem.

A binding pushes a frame with a fresh dict bound under a Shape, writes the
values it hands into the dict's slots, and runs its body on that frame. The
body reads the values through the Shape's refs. Nothing is restored on exit:
the frame is dropped with the body, and a task still holding the body's
Runtime keeps it alive.

- ``_StaticBinding``: the Shape is declared by the user (``let(Tally, ...)``).
- ``_DynamicBinding``: the Shape is generated from the body lambda, one slot
  per parameter, cached per code object. The lambda is called once, at
  construction, with the slots' refs and returns the body tree.

Both are mixins for interactions. An interaction says how many values it
hands (``_dynamic(owner, fn, handed)``) and writes them per run:

    # a sequential binding: one frame for the run, slots written per value
    inner_ctx, data = self._frame(rt.ctx)
    inner = rt.on(inner_ctx)
    for elem in items:
        self._write(data, (elem,))
        body(inner)

    # a concurrent arm: a frame of its own per arm
    body(rt.on(self._push(rt.ctx, (elem,))))

Free form arity, one rule for every dynamic binding: the lambda may take fewer
parameters than the values handed and gets the leading ones, in order; more
parameters than values fails at build.
"""

from __future__ import annotations

import inspect
import types
from functools import cache
from typing import TYPE_CHECKING

from nu.domains.shape import Shape


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from nu.lang.runtime import Context


__all__ = ["_DynamicBinding", "_StaticBinding"]


_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
_VARIADIC = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


class _StaticBinding:
    """Push a frame with a fresh dict under a Shape, write the values, run the body.

    ``_bind_static`` (at build) names the Shape and the slots the values go
    to, in the order they are handed. At run time ``_push`` makes the frame
    and writes the values in one go; ``_frame`` and ``_write`` split it, for
    a binding that keeps one frame for a run and writes a value per step.
    """

    _bind_shape: type[Shape]
    _bind_slots: tuple[str, ...]

    def _bind_static(self, shape: type[Shape], slots: Sequence[str]) -> None:
        """Bind ``shape``, the values handed going to ``slots`` in order. Build time."""
        self._bind_shape = shape
        self._bind_slots = tuple(slots)

    def _frame(self, ctx: Context) -> tuple[Context, dict]:
        """``ctx`` with a frame binding a fresh dict under the Shape, and the dict."""
        data: dict = {}
        return ctx.bind(dict, data, self._bind_shape), data

    def _write(self, data: dict, values: Sequence[object]) -> None:
        """Write ``values`` into the frame's dict, the leading ones when there are more."""
        lowers = _lowers(self._bind_shape)
        for name, value in zip(self._bind_slots, values, strict=False):
            data[name] = lowers[name](value)

    def _push(self, ctx: Context, values: Sequence[object]) -> Context:
        """``ctx`` with a frame holding ``values`` under the Shape."""
        inner, data = self._frame(ctx)
        self._write(data, values)
        return inner


class _DynamicBinding(_StaticBinding):
    """A static binding over a Shape generated from the body lambda.

    ``_dynamic`` (at build) generates the Shape, one slot per lambda
    parameter, calls the lambda once with the slots' refs, and returns the
    body it builds. The values are then written like any static binding's.
    """

    def _dynamic(self, owner: str, fn: object, handed: int) -> object:
        """The body ``fn`` builds; binds the Shape generated from it. Build time.

        Args:
            owner: the interaction's name, for error messages.
            fn: the body lambda, one parameter per value it reads.
            handed: how many values the interaction hands, in order.

        Raises:
            TypeError: ``fn`` is not a function, takes more parameters than
                ``handed`` or a variable list of them, or returns None.
        """
        params = lambda_params(owner, fn)
        if len(params) > handed:
            what = "value" if handed == 1 else "values"
            msg = (
                f"{owner} hands its body {handed} {what}, so its lambda takes at most "
                f"{handed}; got {_spelled(fn)}"
            )
            raise TypeError(msg)
        shape, slots = _generated(fn.__code__, params)  # type: ignore[attr-defined]
        self._bind_static(shape, slots)
        body = fn(*(getattr(shape, s) for s in slots))  # type: ignore[operator]
        if body is None:
            msg = f"{owner}: the lambda returned None, it must return the body tree"
            raise TypeError(msg)
        return body


def lambda_params(owner: str, fn: object) -> tuple[str, ...]:
    """The positional parameter names of the body lambda ``fn``.

    Raises:
        TypeError: ``fn`` is not a function, or takes ``*args``, ``**kwargs``
            or a keyword-only parameter without a default.
    """
    if not isinstance(fn, (types.FunctionType, types.MethodType)):
        msg = f"{owner} needs a function to build its body, got {type(fn).__name__}"
        raise TypeError(msg)
    names: list[str] = []
    for p in inspect.signature(fn).parameters.values():
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
    from nu.domains.shape.dsl import _public_names, _shape_ref_classes

    from .refs import ObjectRef

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
