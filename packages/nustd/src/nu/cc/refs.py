"""PromptRef: Ref addressing a Claude Code prompt endpoint on a Service.

Mirrors nu.http verb refs: `.method(**defaults)` returns a Method declaration
that the ServiceMeta descriptor unwraps at class access; calling the Ref with
kwargs produces a CCPrompt interaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import CCPrompt


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["PromptRef"]


class PromptRef(MethodRef):
    """Addresses a Claude Code agent on a Service, one Ref per agent role.

    Written in a Service class body. The Ref carries no configuration of its
    own beyond its declared defaults: the model, working directory, tool
    allowlist and system prompt come from the ``CCFabric`` provided for the
    owning Service class, so a program can hold several Services each
    standing for a differently-configured agent.

    Notes:
        - Every call spawns a fresh Claude Code session unless it runs
          inside a ``nu.cc.Session`` bracket, which threads the session id
          through so the calls read as one conversation.
        - The Ref needs the ``claude-agent-sdk`` package and a working
          ``claude`` CLI on the machine that evaluates it.

    Example:
        class Agent(nu.Service):
            ask = nu.cc.PromptRef.method(max_turns=1)
        app = nu.With(
            nu.cc.bind(Agent, model="claude-sonnet-4-5", cwd="/tmp"),
            body=nu.print(nu.dict(Agent.ask("name this directory"))["text"]),
        )
        asyncio.run(nu.arun(app))
    """

    @classmethod
    def method(cls, **defaults: object) -> PromptRef:  # type: ignore[override]
        """Declare a prompt endpoint whose defaults every call through it inherits.

        Args:
            **defaults: ``ClaudeAgentOptions`` fields to apply on top of the
                bind for calls through this endpoint (``model``,
                ``max_turns``, ``allowed_tools``, ``permission_mode``, ...).
                A per-call kwarg of the same name wins.

        Notes:
            - Annotated as returning the Ref, but at run time it returns a
              ``Method`` declaration that the ServiceMeta descriptor unwraps
              at class access. The lie makes ``Agent.ask`` type-check as a
              PromptRef.
            - Keys that are not ``ClaudeAgentOptions`` fields are dropped
              silently when the call runs, so a misspelt option is not an
              error, it is a no-op.
        """
        return Method(cls, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, prompt: object, **overrides: object) -> Nu:
        """Build a CCPrompt interaction over one turn's prompt and options.

        Args:
            prompt: the text to send. Stringified at evaluation, so it may
                be a Nu term rather than a literal.
            **overrides: ``ClaudeAgentOptions`` fields for this call only.

        Notes:
            - Keywords beyond the prompt are ``ClaudeAgentOptions`` fields
              applied to this call only.
            - Unlike ChatRef, the prompt is positional and required: there
              is no messages-list form, since the transcript is the
              session's business rather than the caller's.
            - Prompt and overrides land together in one ``Dict`` child, so
              both are resolved at evaluation.
        """
        return CCPrompt(self, Dict.of(prompt=prompt, **overrides))
