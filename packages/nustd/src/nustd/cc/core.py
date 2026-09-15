"""Shared compile thunks: merge defaults + call args, dispatch through CCFabric."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .fabric import CCFabric
from .session import SessionHandle


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["acompile_call", "compile_call"]


def _split(payload: dict, args: dict) -> tuple[str, dict]:
    """Pull `prompt` out; merge endpoint defaults under call overrides."""
    call = dict(args)
    prompt = call.pop("prompt")
    merged = {**payload.get("defaults", {}), **call}
    return str(prompt), merged


def _session(rt: Runtime) -> SessionHandle | None:
    return rt.ctx.get(SessionHandle) if rt.ctx.has(SessionHandle) else None


def compile_call(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: wraps the async fabric call in asyncio.run."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        args = args_thunk(rt)
        prompt, overrides = _split(payload, args)
        fabric = rt.ctx.get(CCFabric, payload["owner_service"])
        handle = _session(rt)
        if handle is not None and handle.session_id:
            overrides.setdefault("resume", handle.session_id)
        result = asyncio.run(fabric.aprompt(prompt, **overrides))
        if handle is not None and result.get("session_id"):
            handle.session_id = result["session_id"]
        return result

    return thunk


def acompile_call(children: tuple[Callable, ...]) -> Callable:
    """Async compile: dispatch through CCFabric."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        args = await args_thunk(rt)
        prompt, overrides = _split(payload, args)
        fabric = rt.ctx.get(CCFabric, payload["owner_service"])
        handle = _session(rt)
        if handle is not None and handle.session_id:
            overrides.setdefault("resume", handle.session_id)
        result = await fabric.aprompt(prompt, **overrides)
        if handle is not None and result.get("session_id"):
            handle.session_id = result["session_id"]
        return result

    return athunk
