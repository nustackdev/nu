"""Compile thunks: merge defaults + call args, dispatch through LLMFabric."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .fabric import LLMFabric


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["acompile_call", "compile_call"]


def _split(payload: dict, args: dict) -> tuple[list[dict], dict]:
    """Merge defaults + call args, pull messages out (or synthesize from `prompt`)."""
    call = dict(args)
    prompt = call.pop("prompt", None)
    messages = call.pop("messages", None)
    if messages is None:
        if prompt is None:
            msg = "LLM call needs `prompt=...` or `messages=[...]`"
            raise ValueError(msg)
        messages = [{"role": "user", "content": str(prompt)}]
    merged = {**payload.get("defaults", {}), **call}
    return list(messages), merged


def compile_call(children: tuple[Callable, ...]) -> Callable:
    """Sync compile: wraps the async fabric call in asyncio.run."""
    ref_thunk, args_thunk = children

    def thunk(rt: Runtime) -> object:
        payload = ref_thunk(rt)
        args = args_thunk(rt)
        messages, overrides = _split(payload, args)
        fabric = rt.ctx.get(LLMFabric, payload["owner_service"])
        return fabric.chat(messages, **overrides)

    return thunk


def acompile_call(children: tuple[Callable, ...]) -> Callable:
    """Async compile: dispatch through LLMFabric."""
    ref_thunk, args_thunk = children

    async def athunk(rt: Runtime) -> object:
        payload = await ref_thunk(rt)
        args = await args_thunk(rt)
        messages, overrides = _split(payload, args)
        fabric = rt.ctx.get(LLMFabric, payload["owner_service"])
        return await fabric.achat(messages, **overrides)

    return athunk
