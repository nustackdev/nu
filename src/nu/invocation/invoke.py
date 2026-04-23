"""Invoke + Invocation -- the python bridge.

Invoke is the one ScalarQuery that calls a python callable. Mode is
inferred from the callable at construction: ``async def`` yields an
ASYNC-only node, plain ``def`` yields a sync-capable node. Effects can be
declared explicitly.

Invocation is a descriptor: drop it on a ``Ref[T]`` or ``TypedNu[T]``
subclass, and method access compiles to an Invoke bound to the named
python method. The target python class is pulled from the generic
parameter via ``__orig_bases__``.
"""

from __future__ import annotations

import inspect
import typing
from typing import TYPE_CHECKING, Any, ClassVar, overload

from ..terms.query import ScalarQuery
from ..terms.ref import Ref
from ..terms.types import Mode, Sentinel


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..terms.interface import Interface
    from ..terms.types import TrackedEffect


__all__ = [
    "FuncCall",
    "FuncCallCmd",
    "Invocation",
    "Invoke",
    "MethodCall",
    "MethodCallCmd",
]


# =============================================================================
# HELPERS
# =============================================================================


def _unwrap(fn: Callable[..., Any]) -> Callable[..., Any]:
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _infer_mode(fn: Callable[..., Any]) -> tuple[Mode, Mode]:
    """(own_mode, func_mode) from a python callable.

    ``async def`` or async generator -> (ASYNC, ASYNC).
    Plain callable -> (BOTH, SYNC).
    """
    target = _unwrap(fn)
    if inspect.iscoroutinefunction(target) or inspect.isasyncgenfunction(target):
        return (Mode.ASYNC, Mode.ASYNC)
    return (Mode.BOTH, Mode.SYNC)


def _extract_py_type(owner: type) -> type | None:
    """Find the generic argument of Ref[T] or TypedNu[T] in owner's MRO."""
    from ..terms.interface import TypedNu

    seen: set[type] = set()

    def walk(cls: type) -> type | None:
        if cls in seen:
            return None
        seen.add(cls)
        for base in getattr(cls, "__orig_bases__", ()):
            origin = typing.get_origin(base)
            if origin is None:
                continue
            if isinstance(origin, type) and issubclass(origin, (Ref, TypedNu)):
                args = typing.get_args(base)
                if args and isinstance(args[0], type):
                    return args[0]
        for base in cls.__mro__[1:]:
            if base is object:
                continue
            found = walk(base)
            if found is not None:
                return found
        return None

    return walk(owner)


# =============================================================================
# INVOKE
# =============================================================================


class Invoke[T](ScalarQuery[T | Sentinel]):
    """Call a python callable with Nu-resolved arguments.

    Args and kwargs are children; they are resolved (first yield each)
    before the callable runs. Sentinels on any operand short-circuit to
    INVALID via ScalarQuery. Async callables are awaited on the async
    path; on the sync path they raise (own_mode=ASYNC blocks sync entry).
    """

    # Class defaults are the widest valid pair; instance __init__ narrows.
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: object,
        effects: frozenset[TrackedEffect] = frozenset(),
        mode: tuple[Mode, Mode] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, *kwargs.values())
        self._fn = fn
        self._kwarg_keys = tuple(kwargs.keys())
        self._effects = effects
        own, func = mode if mode is not None else _infer_mode(fn)
        # Instance-level override; Nu.effective_mode reads via self.
        self.own_mode = own  # type: ignore[misc]
        self.func_mode = func  # type: ignore[misc]

    @property
    def fn(self) -> Callable[..., Any]:
        return self._fn

    @property
    def effects(self) -> frozenset[TrackedEffect]:
        return self._effects

    def _split(self, values: tuple[Any, ...]) -> tuple[tuple[Any, ...], dict[str, Any]]:
        n = len(self._kwarg_keys)
        if n == 0:
            return values, {}
        return values[:-n], dict(zip(self._kwarg_keys, values[-n:], strict=True))

    def apply(self, *values: Any) -> T | Sentinel:  # noqa: ANN401
        pos, kw = self._split(values)
        return self._fn(*pos, **kw)

    async def aapply(self, *values: Any) -> T | Sentinel:  # noqa: ANN401
        pos, kw = self._split(values)
        result = self._fn(*pos, **kw)
        if inspect.isawaitable(result):
            return await result
        return result

    def __repr__(self) -> str:
        name = getattr(self._fn, "__qualname__", None) or getattr(
            self._fn, "__name__", repr(self._fn)
        )
        n = len(self._kwarg_keys)
        children = list(self._children)
        if n:
            pos = children[:-n]
            kw_vals = children[-n:]
            parts = [repr(c) for c in pos] + [
                f"{k}={v!r}" for k, v in zip(self._kwarg_keys, kw_vals, strict=True)
            ]
        else:
            parts = [repr(c) for c in children]
        args = ", ".join(parts)
        return f"Invoke({name}, {args})" if args else f"Invoke({name})"

    def __str__(self) -> str:
        return self.__repr__()


# =============================================================================
# INVOCATION DESCRIPTOR
# =============================================================================


class _RefBoundInvocation[V]:
    """Class-bound: SolanaRef.get_slot(42) -> IntI(Invoke(SolanaRpc.get_slot, SolanaRef(), 42))."""

    __slots__ = ("_fn", "_inv", "_ref_cls")

    def __init__(self, inv: Invocation, ref_cls: type[Ref], fn: Callable[..., Any]) -> None:
        self._inv = inv
        self._ref_cls = ref_cls
        self._fn = fn

    def __call__(self, *args: object, **kwargs: object) -> V:
        target = self._ref_cls()
        return self._inv._return_type(
            Invoke(
                self._fn,
                target,
                *args,
                effects=self._inv._effects,
                mode=self._inv._mode,
                **kwargs,
            )
        )

    def __repr__(self) -> str:
        return f"{self._ref_cls.__name__}.{self._inv._name}"


class _InstanceBoundInvocation[V]:
    """Instance-bound: percentage.to_dec() -> FloatI(Invoke(Percentage.to_dec, percentage))."""

    __slots__ = ("_fn", "_inv", "_owner")

    def __init__(self, inv: Invocation, owner: object, fn: Callable[..., Any]) -> None:
        self._inv = inv
        self._owner = owner
        self._fn = fn

    def __call__(self, *args: object, **kwargs: object) -> V:
        return self._inv._return_type(
            Invoke(
                self._fn,
                self._owner,
                *args,
                effects=self._inv._effects,
                mode=self._inv._mode,
                **kwargs,
            )
        )

    def __repr__(self) -> str:
        return f"{self._owner!r}.{self._inv._name}"


class Invocation[V: "Interface"]:  # noqa: N801
    """Descriptor that compiles attribute access into an Invoke.

    Use on a Ref[T] or TypedNu[T] subclass. At descriptor resolution time,
    the target python class is pulled from the generic argument via
    ``__orig_bases__``; the named method is looked up and its mode is
    inferred. Explicit ``effects`` / ``mode`` override inference.

    The generic parameter must be resolvable (either on the owner class
    directly or via its MRO). If it is not, supply ``mode=`` explicitly.
    """

    def __init__(
        self,
        return_type: type[V],
        name: str | None = None,
        *,
        effects: frozenset[TrackedEffect] = frozenset(),
        mode: tuple[Mode, Mode] | None = None,
    ) -> None:
        self._return_type = return_type
        self._explicit_name = name
        self._name: str = name or ""
        self._effects = effects
        self._mode = mode
        self._fn_cache: dict[type, Callable[..., Any]] = {}

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._name = self._explicit_name or attr_name

    def _resolve_fn(self, cls: type) -> Callable[..., Any]:
        cached = self._fn_cache.get(cls)
        if cached is not None:
            return cached
        py_type = _extract_py_type(cls)
        if py_type is None:
            msg = (
                f"Invocation({self._return_type.__name__}, {self._name!r}) on "
                f"{cls.__name__}: cannot locate the underlying python type "
                "(no Ref[T] or TypedNu[T] in the MRO). Declare the generic "
                "parameter on the owning class."
            )
            raise TypeError(msg)
        fn = getattr(py_type, self._name, None)
        if fn is None:
            msg = f"{py_type.__name__} has no attribute {self._name!r}"
            raise TypeError(msg)
        self._fn_cache[cls] = fn
        return fn

    @overload
    def __get__(self, obj: None, objtype: type) -> _RefBoundInvocation[V]: ...
    @overload
    def __get__(
        self, obj: object, objtype: type | None = None
    ) -> _InstanceBoundInvocation[V]: ...

    def __get__(
        self, obj: object | None, objtype: type | None = None
    ) -> Invocation[V] | _RefBoundInvocation[V] | _InstanceBoundInvocation[V]:
        if obj is None:
            if objtype is not None and issubclass(objtype, Ref):
                fn = self._resolve_fn(objtype)
                return _RefBoundInvocation(self, objtype, fn)
            return self
        fn = self._resolve_fn(type(obj))
        return _InstanceBoundInvocation(self, obj, fn)

    def __repr__(self) -> str:
        return f"Invocation({self._return_type.__name__}, {self._name!r})"


# =============================================================================
# COMPAT SHIMS
#
# FuncCall / MethodCall predate Invoke. They remain as public names because a
# lot of code uses them; under the hood every call builds an Invoke. The Cmd
# variants are structurally identical for now (Command role distinction is a
# later refinement).
# =============================================================================


FuncCall = Invoke
FuncCallCmd = Invoke


def MethodCall(
    target: object,
    name: str,
    *args: object,
    effects: frozenset[TrackedEffect] = frozenset(),
    mode: tuple[Mode, Mode] | None = None,
    **kwargs: object,
) -> Invoke:
    """Call a named method on target. Sugar for Invoke(T.name, target, *args).

    Resolves ``T`` from target's python class (via ``_extract_py_type`` when
    target is a Nu carrying a generic). Falls back to a runtime-getattr
    closure when the type can't be inferred; explicit ``mode=`` is needed
    there if the method is async.
    """
    py_type = _extract_py_type(type(target))
    fn_candidate = getattr(py_type, name, None) if py_type is not None else None

    if fn_candidate is None:
        def fn(t: Any, *a: Any, **kw: Any) -> Any:  # noqa: ANN401
            return getattr(t, name)(*a, **kw)

        fn.__name__ = name
        fn.__qualname__ = name
        return Invoke(fn, target, *args, effects=effects, mode=mode, **kwargs)

    return Invoke(fn_candidate, target, *args, effects=effects, mode=mode, **kwargs)


MethodCallCmd = MethodCall
