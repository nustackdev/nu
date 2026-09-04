"""Nu Claude Code fabric.

Surface:
    - CCFabric: holds a ClaudeAgentOptions template + runs one query per prompt call.
    - PromptRef: MethodRef for a Claude Code prompt endpoint on a Service.
    - CCPrompt: the interaction produced when a PromptRef is called.
    - bind(service_cls, **options): Provide the CCFabric tagged by the Service class.
    - Session: bracket that makes every prompt inside it continue one conversation.

Both sync and async are supported; prefer `nu.arun` for real use so cc calls
don't block the event loop (streaming, UI ticks, parallel prompts all need it).
Sync is fine for one-off scripts.

Example::

    class Agent(nu.Service):
        ask = nu.cc.PromptRef.method()

    app = nu.With(
        nu.cc.bind(Agent, model="claude-sonnet-4-5", permission_mode="acceptEdits"),
        body=nu.print(nu.Dict(Agent.ask(prompt="write a haiku about rust"))["text"]),
    )

    asyncio.run(nu.arun(app))
"""

from __future__ import annotations

from .fabric import CCFabric
from .interactions import CCPrompt
from .presets import bind
from .refs import PromptRef
from .session import Session, SessionHandle


__all__ = ["CCFabric", "CCPrompt", "PromptRef", "Session", "SessionHandle", "bind"]
