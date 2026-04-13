"""Function and method invocation ops.

FuncCall / FuncCallOp / FuncCallCmd:
    Call a callable with arguments.

MethodCall / MethodCallOp / MethodCallCmd:
    Call a named method on a target instance.

All variants support:
- Args/kwargs as Terms or literals
- Sentinel propagation (INVALID on sentinel operands)
- Auto-await for async callables/methods
"""

from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from nu.terms import INVALID, Op, Sentinel, is_sentinel


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.context import Context


__all__ = [
    "FuncCall",
    "FuncCallCmd",
    "FuncCallOp",
    "MethodCall",
    "MethodCallCmd",
    "MethodCallOp",
]


# =============================================================================
# FUNCTION CALL
# =============================================================================


class FuncCall[T](Op[T | Sentinel]):
    """Call a function with arguments.

    Arguments can be Terms or literals — Terms are resolved before
    the function is called. Auto-awaits async results.
    Sentinel propagation: returns INVALID if any arg is a sentinel.

    Use ``FuncCallOp`` for pure calls, ``FuncCallCmd`` for impure.

    Example::

        FuncCallOp(datetime.now)
        FuncCallCmd(requests.get, url_term, timeout=5)
    """

    def __init__(self, func: Callable[..., Any], *args: object, **kwargs: object) -> None:
        super().__init__(*args, *kwargs.values())
        self._func = func
        self._kwarg_keys = tuple(kwargs.keys())

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Resolve args, propagate sentinels, call function, auto-await."""
        values: list[Any] = []
        for child in self.children:
            val = await child.execute(ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)

        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            pos_args = values[:-num_kwargs]
            kw_args = dict(zip(self._kwarg_keys, values[-num_kwargs:], strict=True))
        else:
            pos_args = values
            kw_args = {}

        result = self._func(*pos_args, **kw_args)
        if isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        func_name = getattr(self._func, "__name__", repr(self._func))
        args = ", ".join(repr(c) for c in self._children)
        cls = self.__class__.__name__
        return f"{cls}({func_name}, {args})" if args else f"{cls}({func_name})"


class FuncCallOp[T](FuncCall[T]):
    """Pure function call. No side effects."""


class FuncCallCmd[T](FuncCall[T]):
    """Impure function call. May have side effects."""


# =============================================================================
# METHOD CALL
# =============================================================================


class MethodCall[T](Op[T | Sentinel]):
    """Call a named method on a target with arguments.

    Target is the first child Nu. Args/kwargs are remaining children.
    Method name is a static string. Auto-awaits async results.
    Sentinel propagation: returns INVALID if any child is a sentinel.

    Use ``MethodCallOp`` for pure calls, ``MethodCallCmd`` for impure.

    Example::

        MethodCallOp(my_str_value, "upper")
        MethodCallCmd(api_client, "fetch", url_term)
    """

    def __init__(self, target: object, method_name: str, *args: object, **kwargs: object) -> None:
        super().__init__(target, *args, *kwargs.values())
        self._method_name = method_name
        self._kwarg_keys = tuple(kwargs.keys())

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Resolve children, propagate sentinels, call method, auto-await."""
        values: list[Any] = []
        for child in self.children:
            val = await child.execute(ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)

        target = values[0]
        remaining = values[1:]

        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            pos_args = remaining[:-num_kwargs]
            kw_args = dict(zip(self._kwarg_keys, remaining[-num_kwargs:], strict=True))
        else:
            pos_args = remaining
            kw_args = {}

        result = getattr(target, self._method_name)(*pos_args, **kw_args)
        if isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        parts = [repr(c) for c in self._children]
        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            positional = parts[: len(parts) - num_kwargs]
            kw_values = parts[-num_kwargs:]
            kw_parts = [f"{k}={v}" for k, v in zip(self._kwarg_keys, kw_values, strict=True)]
            all_parts = positional + kw_parts
        else:
            all_parts = parts
        args_str = ", ".join(all_parts)
        cls = self.__class__.__name__
        if args_str:
            return f"{cls}(.{self._method_name}, {args_str})"
        return f"{cls}(.{self._method_name})"


class MethodCallOp[T](MethodCall[T]):
    """Pure method call. No side effects."""


class MethodCallCmd[T](MethodCall[T]):
    """Impure method call. May have side effects."""
