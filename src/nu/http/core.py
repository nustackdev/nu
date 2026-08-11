"""Shared wire logic for the 5 HTTP interactions: path formatting + compile thunks.

`compile_call` / `acompile_call` build the sync/async thunks used by every
interaction's `_compile` / `_acompile`. They read the endpoint payload from
child 0, the call kwargs from child 1, look up the tagged HttpFabric on the
runtime context, and dispatch the request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .fabric import HttpFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["acompile_call", "compile_call"]


def _format_path(path: str, kwargs: dict) -> tuple[str, dict]:
    """Substitute {name} placeholders from kwargs; return (path, remaining kwargs)."""
    remaining = dict(kwargs)
    formatted = path
    for key in list(remaining):
        placeholder = "{" + key + "}"
        if placeholder in formatted:
            formatted = formatted.replace(placeholder, str(remaining.pop(key)))
    return formatted, remaining


def _split_kwargs(verb: str, path: str, defaults: dict, kwargs: dict) -> tuple[str, dict]:
    """Format path, merge defaults + call kwargs, route to params or json body."""
    formatted, call_rem = _format_path(path, kwargs)
    merged = {**defaults, **call_rem}
    if verb in ("GET", "DELETE"):
        return formatted, {"params": merged}
    return formatted, {"json": merged}


def compile_call(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: format wire args, dispatch through the tagged HttpFabric."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        args = args_thunk(rt)
        verb = payload["verb"]
        path, wire = _split_kwargs(verb, payload["path"], payload["defaults"], args)
        fabric = rt.ctx.get(HttpFabric, payload["owner_service"])
        return fabric.request(verb, path, **wire)

    return thunk


def acompile_call(children: tuple[Callable, ...]) -> Callable:
    """Async compile: format wire args, dispatch through the tagged HttpFabric."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        args = await args_thunk(rt)
        verb = payload["verb"]
        path, wire = _split_kwargs(verb, payload["path"], payload["defaults"], args)
        fabric = rt.ctx.get(HttpFabric, payload["owner_service"])
        return await fabric.arequest(verb, path, **wire)

    return athunk
