"""Shared compile thunks: merge defaults + call args, dispatch through CCFabric."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

from .fabric import CCFabric
from .session import SessionHandle


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["acompile_call", "acompile_new_session", "compile_call", "compile_new_session"]


def _split(payload: dict, args: dict) -> tuple[str, dict]:
    """Pull `prompt` out; merge endpoint defaults under call overrides."""
    call = dict(args)
    prompt = call.pop("prompt")
    merged = {**payload.get("defaults", {}), **call}
    return str(prompt), merged


def _session(rt: Runtime) -> SessionHandle | None:
    return rt.ctx.fabrics.get(SessionHandle) if rt.ctx.fabrics.has(SessionHandle) else None


def compile_call(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: one ``asyncio.run`` per prompt, through the Session if one is open."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        prompt, overrides = _split(payload, args_thunk(rt))
        fabric = rt.ctx.fabrics.get(CCFabric, payload["owner_service"])
        handle = _session(rt)
        if handle is None:
            return asyncio.run(fabric.aprompt(prompt, **overrides))
        return handle.prompt(fabric, prompt, overrides)

    return thunk


def acompile_call(children: tuple[Callable, ...]) -> Callable:
    """Async compile: one-shot outside a Session, a turn on its process inside one."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        prompt, overrides = _split(payload, await args_thunk(rt))
        fabric = rt.ctx.fabrics.get(CCFabric, payload["owner_service"])
        handle = _session(rt)
        if handle is None:
            return await fabric.aprompt(prompt, **overrides)
        return await handle.aprompt(fabric, prompt, overrides)

    return athunk


def compile_new_session(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: a fresh conversation id."""

    def thunk(rt: Runtime) -> object:
        return str(uuid.uuid4())

    return thunk


def acompile_new_session(children: tuple[Callable, ...]) -> Callable:
    """Async compile: a fresh conversation id."""

    async def athunk(rt: Runtime) -> object:
        return str(uuid.uuid4())

    return athunk
