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

Both are mixins for interactions with one body. An interaction says how many
values it hands (``_dynamic(owner, fn, handed)``) and writes them per run:

    # a sequential binding: one frame for the run, slots written per value
    inner_ctx, data = self._frame(rt.ctx)
    inner = rt.on(inner_ctx)
    for elem in items:
        self._write(data, (elem,))
        body(inner)

    # a concurrent arm: a frame of its own per arm
    body(rt.on(self._push(rt.ctx, (elem,))))

An interaction with several bodies that each read what it hands (``Retry``'s
hooks, ``ReactWhile``'s condition and body) keeps one :class:`Binding` per
body, from :func:`dynamic`; the mixin is the one-body case of the same thing.

Free form arity, one rule for every dynamic binding: the lambda may take fewer
parameters than the values handed and gets the leading ones, in order; more
parameters than values fails at build. A body given as a plain tree, not a
lambda, is a lambda taking none: it reads nothing it is handed, and its
binding pushes no frame.

Lives in ``nu.lang`` rather than ``nu.mem`` so the core interactions can
subclass it while ``nu.mem`` is still loading; the Shape machinery it stands
on is imported when a Shape is first generated.
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


__all__ = [
    "NO_BINDING",
    "Binding",
    "_DynamicBinding",
    "_StaticBinding",
    "dynamic",
    "is_builder",
    "lambda_params",
    "named",
]


_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
_VARIADIC = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)


class Binding:
    """One binding: the Shape a body reads and the slots the handed values go to.

    Immutable and built once, at construction. ``push`` makes a frame and
    writes the values in one go; ``frame`` and ``write`` split it, for a
    binding that keeps one frame for a run and writes a value per step.

    A binding with no Shape (:data:`NO_BINDING`, a body that reads nothing)
    pushes no frame: ``frame`` and ``push`` hand ``ctx`` back as it is.
    """

    __slots__ = ("shape", "slots")

    shape: type[Shape] | None
    slots: tuple[str, ...]

    def __init__(self, shape: type[Shape] | None, slots: Sequence[str] = ()) -> None:
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "slots", tuple(slots))

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

    def frame(self, ctx: Context) -> tuple[Context, dict]:
        """``ctx`` with a frame binding a fresh dict under the Shape, and the dict."""
        data: dict = {}
        if self.shape is None:
            return ctx, data
        return ctx.bind(dict, data, self.shape), data

    def write(self, data: dict, values: Sequence[object]) -> None:
        """Write ``values`` into the frame's dict, the leading ones when there are more."""
        if self.shape is None:
            return
        lowers = _lowers(self.shape)
        for name, value in zip(self.slots, values, strict=False):
            data[name] = lowers[name](value)

    def push(self, ctx: Context, values: Sequence[object]) -> Context:
        """``ctx`` with a frame holding ``values`` under the Shape."""
        if self.shape is None:
            return ctx
        inner, data = self.frame(ctx)
        self.write(data, values)
        return inner

    def __repr__(self) -> str:
        if self.shape is None:
            return "Binding()"
        return f"Binding({self.shape.__name__}, {list(self.slots)})"


NO_BINDING = Binding(None)
"""The binding of a body that reads nothing: a plain tree, or a lambda taking no parameter."""


def dynamic(owner: str, fn: object, handed: int) -> tuple[object, Binding]:
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
        return fn, NO_BINDING
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
        binding = Binding(shape, slots)
        refs = [getattr(shape, s) for s in slots]
    else:
        binding, refs = NO_BINDING, []
    body = fn(*refs)  # type: ignore[operator]
    if body is None:
        msg = f"{owner}: the lambda returned None, it must return the body tree"
        raise TypeError(msg)
    return body, binding


def named(owner: str, fn: object, values: Mapping[str, object]) -> tuple[object, Binding, tuple]:
    """The body ``fn`` builds, its binding, and ``values`` in slot order. Build time.

    The values are given by parameter name, the rule ``let`` and the
    Teleports share: every parameter takes a value and every value names a
    parameter. A plain tree (not a lambda) takes no values and binds nothing.

    Raises:
        TypeError: a parameter has no value, a value names no parameter, a
            tree is given values, or ``fn`` breaks :func:`dynamic`'s rules.
    """
    if not is_builder(fn):
        if values:
            msg = (
                f"{owner}: a tree body takes no values; got {list(values)}, pass a lambda over them"
            )
            raise TypeError(msg)
        return fn, NO_BINDING, ()
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
    body, binding = dynamic(owner, fn, len(params))
    return body, binding, tuple(values[p] for p in params)


class _StaticBinding:
    """Push a frame with a fresh dict under a Shape, write the values, run the body.

    ``_bind_static`` (at build) names the Shape and the slots the values go
    to, in the order they are handed. At run time ``_push`` makes the frame
    and writes the values in one go; ``_frame`` and ``_write`` split it, for
    a binding that keeps one frame for a run and writes a value per step.
    """

    _binding: Binding

    def _bind_static(self, shape: type[Shape] | None, slots: Sequence[str]) -> None:
        """Bind ``shape``, the values handed going to ``slots`` in order. Build time."""
        self._binding = NO_BINDING if shape is None else Binding(shape, slots)

    @property
    def _bind_shape(self) -> type[Shape] | None:
        return self._binding.shape

    @property
    def _bind_slots(self) -> tuple[str, ...]:
        return self._binding.slots

    def _frame(self, ctx: Context) -> tuple[Context, dict]:
        """``ctx`` with a frame binding a fresh dict under the Shape, and the dict."""
        return self._binding.frame(ctx)

    def _write(self, data: dict, values: Sequence[object]) -> None:
        """Write ``values`` into the frame's dict, the leading ones when there are more."""
        self._binding.write(data, values)

    def _push(self, ctx: Context, values: Sequence[object]) -> Context:
        """``ctx`` with a frame holding ``values`` under the Shape."""
        return self._binding.push(ctx, values)


class _DynamicBinding(_StaticBinding):
    """A static binding over a Shape generated from the body lambda.

    ``_dynamic`` (at build) generates the Shape, one slot per lambda
    parameter, calls the lambda once with the slots' refs, and returns the
    body it builds. The values are then written like any static binding's.
    """

    def _dynamic(self, owner: str, fn: object, handed: int) -> object:
        """The body ``fn`` builds; binds the Shape generated from it. Build time.

        A plain tree passes through as the body and binds nothing.

        Args:
            owner: the interaction's name, for error messages.
            fn: the body lambda, one parameter per value it reads, or a tree.
            handed: how many values the interaction hands, in order.

        Raises:
            TypeError: ``fn`` takes more parameters than ``handed`` or a
                variable list of them, or returns None.
        """
        body, self._binding = dynamic(owner, fn, handed)
        return body


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
