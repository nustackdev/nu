"""``InteractionFactory``: the generic mechanism for building atoms from callables.

One mechanism, ``InteractionFactory``: pass a base kind, a name, and a callable,
get back a real ``Nu`` subclass wired with sync / async thunks, sentinel
handling, and declared attributes. It collapses the "resolve the children, call
a Python function, return the result" boilerplate that most non-hot
interactions are.

``nu.core`` atoms stay hand-written end-to-end (a clean thunk, no extra hop)
for the hot path. The factory is for the rest - the ``nu.std`` library and
anything else that just bridges to a host callable.

A method call needs no special support here: an *unbound* method is a plain
callable whose first argument is the receiver, so ``d.weekday()`` is
``date.weekday(d)``. Bind the unbound method and pass the receiver as the
first child. ``MethodFactory`` (in ``.methods``) is the sugar over that idiom
when you want to name the method instead of writing a lambda.

Supported base kinds: ``ScalarQuery``, ``Command``, ``ScalarAction``. Stream
(query or action), reduction, flow, and span have non-trivial dispatch shapes
the factory does not reproduce.

Yield semantics follow the base:
- ``ScalarQuery`` / ``ScalarAction`` -- the function's return value is yielded.
- ``Command`` -- the function runs for its side effect; the thunk returns ``None``.

Arguments. Children passed positionally land as positional args to the
callable; children passed by keyword land as keyword args. The split is
recorded in the atom's payload so ``compile`` can rebuild the call::

    DateOf(2026, 6, 30)            -> date(2026, 6, 30)
    DatetimeReplace(dt, hour=9)    -> datetime.replace(dt, hour=9)

Sync vs async is inferred from the callable. An ``async def`` produces a
class whose ``compile`` falls back to the base (which raises) and whose
``acompile`` awaits the function; the class also declares
``requires_async = True``. A plain ``def`` produces both paths.

Sentinel handling:
- ``propagate_sentinels=True`` (default) -- a resolved child that is ``EMPTY``
  or ``INVALID`` short-circuits the thunk without invoking the function.
  ``ScalarQuery`` / ``ScalarAction`` return ``INVALID``; ``Command`` returns
  ``None``.
- ``propagate_sentinels=False`` -- sentinels pass through to the function.

Declared attributes are passed by keyword. Raw values are wrapped in
``Declared``; pre-built ``Attribute`` instances (including computed
``Synthesized`` / ``Inherited``) pass through unchanged::

    Add = InteractionFactory(
        ScalarQuery, "Add", lambda *xs: sum(xs),
        commutative=True, associative=True,
    )
    Set = InteractionFactory(
        Command, "Set", lambda ref, value: ...,
        mutates=frozenset({0}),
    )

Note: IDEs and static type checkers see the return as ``type[B]`` where ``B``
is the base; they cannot show a docstring or signature specific to the
synthesised class. Hand-write the class when IDE discoverability matters.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, cast

from nu.engine.structure import Attribute, Declared
from nu.lang.kinds import Command
from nu.lang.nu import Nu
from nu.lang.sentinels import EMPTY, INVALID

from .helpers import _ALLOWED_BASES, _REJECTED_BASES


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["InteractionFactory"]


def InteractionFactory[B: Nu](  # noqa: N802 -- a class factory; reads as a class at the call site
    base: type[B],
    name: str,
    fn: Callable[..., object],
    *,
    propagate_sentinels: bool = True,
    **attributes: object,
) -> type[B]:
    """Build a ``Nu`` subclass bound to a Python callable.

    See the module docstring for semantics. Returns a fresh class named
    ``name`` whose metaclass collects every declared attribute (and
    ``requires_async`` for ``async def`` targets).
    """
    if not isinstance(base, type):
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
    if not issubclass(base, _ALLOWED_BASES):
        msg = (
            f"InteractionFactory base must subclass ScalarQuery, Command, "
            f"or ScalarAction (got {base!r})"
        )
        raise TypeError(msg)

    is_async = inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn)
    is_command = issubclass(base, Command)
    void_value: object = None  # commands yield nothing
    sentinel_value: object = void_value if is_command else INVALID

    namespace: dict[str, object] = {}
    for attr_name, value in attributes.items():
        if isinstance(value, Attribute):
            if value.name is None:
                value.name = attr_name
            namespace[f"_{attr_name}"] = value
        else:
            namespace[f"_{attr_name}"] = Declared(value=value, name=attr_name)

    if is_async:
        namespace["_requires_async"] = Declared(value=True, name="requires_async")

    def init_method(self: Nu, *args: object, **kwargs: object) -> None:
        Nu.__init__(self, *args, *kwargs.values())
        self._payload = {"npos": len(args), "kwkeys": tuple(kwargs.keys())}

    namespace["__init__"] = init_method

    if not is_async:

        def compile_method(
            self: Nu,
            nid: int,
            children: tuple[Callable[[Runtime], object], ...],
        ) -> Callable[[Runtime], object]:
            npos = cast("int", self._payload.get("npos", len(children)))
            kwkeys = cast("tuple[str, ...]", self._payload.get("kwkeys", ()))
            pos_ts = children[:npos]
            kw_ts = children[npos:]

            def thunk(rt: Runtime) -> object:
                args: list[object] = []
                for ct in pos_ts:
                    v = ct(rt)
                    if propagate_sentinels and (v is EMPTY or v is INVALID):
                        return sentinel_value
                    args.append(v)
                kwargs: dict[str, object] = {}
                for k, kt in zip(kwkeys, kw_ts, strict=True):
                    v = kt(rt)
                    if propagate_sentinels and (v is EMPTY or v is INVALID):
                        return sentinel_value
                    kwargs[k] = v
                result = fn(*args, **kwargs)
                return void_value if is_command else result

            return thunk

        namespace["_compile"] = compile_method

    def acompile_method(
        self: Nu,
        nid: int,
        children: tuple[Callable[[Runtime], object], ...],
    ) -> Callable[[Runtime], object]:
        npos = cast("int", self._payload["npos"])
        kwkeys = cast("tuple[str, ...]", self._payload["kwkeys"])
        pos_ts = children[:npos]
        kw_ts = children[npos:]

        async def athunk(rt: Runtime) -> object:
            args: list[object] = []
            for ct in pos_ts:
                v = await ct(rt)  # type: ignore[misc]
                if propagate_sentinels and (v is EMPTY or v is INVALID):
                    return sentinel_value
                args.append(v)
            kwargs: dict[str, object] = {}
            for k, kt in zip(kwkeys, kw_ts, strict=True):
                v = await kt(rt)  # type: ignore[misc]
                if propagate_sentinels and (v is EMPTY or v is INVALID):
                    return sentinel_value
                kwargs[k] = v
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return void_value if is_command else result

        return athunk

    namespace["_acompile"] = acompile_method
    namespace["__doc__"] = f"Built atom calling {getattr(fn, '__qualname__', fn)!r}."

    return type(name, (base,), namespace)  # type: ignore[return-value]
