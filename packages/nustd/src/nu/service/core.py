"""Shared dispatch for the Service interactions.

Scalar path: getattr(target, name)(**kwargs); await if awaitable.
Stream path: getattr(target, name)(**kwargs) must return an iterable or
async iterable; bridged to the compile-time iterator/async-iterator shape
Nu expects.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from .fabric import ServiceFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "acompile_scalar",
    "acompile_stream",
    "acompile_void",
    "compile_scalar",
    "compile_stream",
    "compile_void",
]


def _lookup(rt: Runtime, payload: dict) -> tuple[object, str]:
    fabric: ServiceFabric = rt.ctx.get(ServiceFabric, payload["owner_service"])
    attr = payload.get("target_attr") or payload["name"]
    return fabric.resolve(attr), attr


def _merge(payload: dict, kwargs: dict) -> dict:
    defaults = payload.get("defaults") or {}
    return {**defaults, **kwargs}


def compile_scalar(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: dispatch scalar target method; refuse async return."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        kwargs = args_thunk(rt)
        fn, name = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isawaitable(result):
            msg = f"Service scalar '{name}' returned an awaitable under nu.run; use nu.arun"
            raise RuntimeError(msg)
        return result

    return thunk


def acompile_scalar(children: tuple[Callable, ...]) -> Callable:
    """Async compile: dispatch scalar target method; await if awaitable."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        kwargs = await args_thunk(rt)
        fn, _ = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isawaitable(result):
            return await result
        return result

    return athunk


def compile_void(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: dispatch void target method; drop the return value."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> None:
        payload = ref_thunk(rt)
        kwargs = args_thunk(rt)
        fn, name = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isawaitable(result):
            msg = f"Service command '{name}' returned an awaitable under nu.run; use nu.arun"
            raise RuntimeError(msg)
        return None

    return thunk


def acompile_void(children: tuple[Callable, ...]) -> Callable:
    """Async compile: dispatch void target method; await + drop the return."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> None:
        payload = await ref_thunk(rt)
        kwargs = await args_thunk(rt)
        fn, _ = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isawaitable(result):
            await result
        return None

    return athunk


def compile_stream(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: dispatch stream target method; refuse async-gen return."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        kwargs = args_thunk(rt)
        fn, name = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isasyncgen(result):
            msg = f"Service stream '{name}' returned an async generator under nu.run; use nu.arun"
            raise RuntimeError(msg)
        return iter(result)

    return thunk


def acompile_stream(children: tuple[Callable, ...]) -> Callable:
    """Async compile: bridge sync-iterables and async-generators to async iteration."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        kwargs = await args_thunk(rt)
        fn, _ = _lookup(rt, payload)
        result = fn(**_merge(payload, kwargs))
        if inspect.isasyncgen(result):
            return result

        async def agen() -> object:
            if inspect.isawaitable(result):
                inner = await result
            else:
                inner = result
            if inspect.isasyncgen(inner):
                async for x in inner:
                    yield x
            else:
                for x in inner:
                    yield x

        return agen()

    return athunk
