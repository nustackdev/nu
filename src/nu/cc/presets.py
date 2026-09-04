"""bind(): Provide a CCFabric for a Service."""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import CCFabric


__all__ = ["bind"]


def bind(service_cls: type, **defaults: object) -> Provide:
    """Configure the Claude Code agent a Service's PromptRefs run against.

    What it provides is tagged by the Service class, which is how a PromptRef
    declared on that class finds its fabric, and how one program can run
    several agents with different tools, directories or system prompts side
    by side.

    Args:
        service_cls: the Service whose PromptRefs this agent serves.
        **defaults: ``ClaudeAgentOptions`` fields - ``model``, ``cwd``,
            ``allowed_tools``, ``system_prompt``, ``permission_mode``,
            ``max_turns``, and the rest. Pass ``options=`` with a built
            ``ClaudeAgentOptions`` instead to bypass the kwargs entirely.

    Notes:
        - The kwargs are ``ClaudeAgentOptions`` fields - ``model``, ``cwd``,
          ``allowed_tools``, ``system_prompt``, ``permission_mode``,
          ``max_turns`` and the rest - or a single ``options=`` holding a
          built ``ClaudeAgentOptions``.
        - These are the outermost layer: declaration defaults sit on top of
          them and per-call overrides on top of those.
        - Unlike the LLM fabric there is no client to open, so the
          ``With`` block costs nothing until a prompt actually runs.
        - Everything here reaches the ``ClaudeAgentOptions`` constructor as
          written, so a bad key raises when the block is entered - unlike a
          per-call override, which is dropped silently.
        - ``options=`` and loose kwargs do not combine: given both, the
          built options object is used and the kwargs are ignored.

    Yields:
        A Provide to hand to ``nu.With``.

    Example:
        app = nu.With(nu.cc.bind(Agent, model="claude-sonnet-4-5", cwd="/srv/repo"), body=...)
    """
    return Provide(CCFabric, defaults, tag=service_cls)
