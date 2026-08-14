"""bind(): Provide a CCFabric for a Service."""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import CCFabric


__all__ = ["bind"]


def bind(service_cls: type, **defaults: object) -> Provide:
    """Provide a CCFabric tagged by the service class.

    Kwargs pass through to `ClaudeAgentOptions` (model, cwd, allowed_tools,
    system_prompt, permission_mode, max_turns, ...). Pass `options=...` to
    hand a fully-built ClaudeAgentOptions instead.
    """
    return Provide(CCFabric, defaults, tag=service_cls)
