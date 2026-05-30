"""Class factory for declaring Interaction kinds from Python callables.

Most concrete atoms in ``nu2.core`` boil down to "resolve the children,
call a Python function, return the result". ``InteractionFactory``
collapses the boilerplate: pass a base kind, a name, and a function, and
you get back a real ``Nu`` subclass wired with sync/async thunks,
sentinel handling, and any declared attributes.

Supported base kinds: ``ScalarQuery``, ``Command``, ``ScalarAction``.
Stream, reduction, flow, and span have non-trivial dispatch shapes that
the factory does not try to reproduce.

Yield semantics follow the base:
- ``ScalarQuery`` / ``ScalarAction`` -- the function's return value is the
  yielded value.
- ``Command`` -- the function is called for its side effect; the thunk
  returns ``None``.

Sync vs async is inferred from the callable. An ``async def`` produces a
class whose ``compile`` falls back to the base (which raises) and whose
``acompile`` awaits the function; the class also declares
``requires_async = True``. A plain ``def`` produces both paths.

Sentinel handling:
- ``propagate_sentinels=True`` (default) -- if any resolved child is
  ``EMPTY`` or ``INVALID``, the thunk short-circuits without invoking the
  function. ``ScalarQuery`` / ``ScalarAction`` return ``INVALID``;
  ``Command`` returns ``None``.
- ``propagate_sentinels=False`` -- sentinels pass through to the function.

Attribute declarations are passed by keyword. Raw values are wrapped in
``Declared``; pre-built ``Attribute`` instances pass through unchanged::

    Add = InteractionFactory(
        ScalarQuery, "Add",
        lambda *xs: sum(xs),
        commutative=True,
        associative=True,
    )
    Set = InteractionFactory(
        Command, "Set",
        lambda ref, value: ...,
        mutates=frozenset({0}),
    )

Note: IDEs and static type checkers see the factory's return as
``type[B]`` where ``B`` is the base you passed. They cannot show a
docstring or signature specific to the synthesised class. Hand-write the
class when IDE discoverability matters.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute, Declared

from .kinds import Command, Flow, Reduction, ScalarAction, ScalarQuery, Span, StreamQuery
from .nu import Nu
from .sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from .runtime import Runtime


__all__ = ["InteractionFactory"]


_ALLOWED_BASES: tuple[type, ...] = (ScalarQuery, Command, ScalarAction)
_REJECTED_BASES: tuple[type, ...] = (StreamQuery, Reduction, Flow, Span)


def InteractionFactory[B: Nu](  # noqa: N802 -- a class factory; reads as a class at the call site
    base: type[B],
    name: str,
    fn: Callable[..., object],
    *,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> type[B]:
    """Build a ``Nu`` subclass bound to a Python callable.

    See module docstring for semantics. Returns a fresh class named
    ``name`` whose metaclass-driven attribute collection picks up every
    declared attribute (and ``requires_async`` for ``async def`` targets).
    """
    if not isinstance(base, type) or not issubclass(base, _ALLOWED_BASES):
        msg = (
            f"InteractionFactory base must subclass ScalarQuery, Command, "
            f"or ScalarAction (got {base!r})"
        )
        raise TypeError(msg)
    if issubclass(base, _REJECTED_BASES):
        msg = (
            f"InteractionFactory does not support stream, reduction, flow, "
            f"or span kinds (got {base.__name__})"
        )
        raise TypeError(msg)

    is_async = inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn)
    is_command = issubclass(base, Command)
    void_value: object = None  # commands yield nothing
    sentinel_value: object = void_value if is_command else INVALID

    namespace: dict[str, object] = {}
    for attr_name, value in attributes.items():
        namespace[attr_name] = value if isinstance(value, Attribute) else Declared(value=value)

    if is_async:
        namespace["requires_async"] = Declared(value=True)

    if not is_async:

        def compile_method(
            self: Nu,
            nid: int,
            children: tuple[Callable[[Runtime], object], ...],
        ) -> Callable[[Runtime], object]:
            def thunk(rt: Runtime) -> object:
                args: list[object] = []
                for ct in children:
                    v = ct(rt)
                    if propagate_sentinels and (v is EMPTY or v is INVALID):
                        return sentinel_value
                    args.append(v)
                result = fn(*args)
                return void_value if is_command else result

            return thunk

        namespace["compile"] = compile_method

    def acompile_method(
        self: Nu,
        nid: int,
        children: tuple[Callable[[Runtime], object], ...],
    ) -> Callable[[Runtime], object]:
        async def athunk(rt: Runtime) -> object:
            args: list[object] = []
            for ct in children:
                v = await ct(rt)  # type: ignore[misc]
                if propagate_sentinels and (v is EMPTY or v is INVALID):
                    return sentinel_value
                args.append(v)
            result = fn(*args)
            if inspect.isawaitable(result):
                result = await result
            return void_value if is_command else result

        return athunk

    namespace["acompile"] = acompile_method
    namespace["__doc__"] = f"Built atom calling {getattr(fn, '__qualname__', fn)!r}."

    return type(name, (base,), namespace)  # type: ignore[return-value]
