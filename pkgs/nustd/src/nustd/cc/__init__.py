"""Nu Claude Code fabric.

Surface:
    - CCFabric: holds a ClaudeAgentOptions template + makes the calls into the SDK.
    - PromptRef: MethodRef for a Claude Code prompt endpoint on a Service.
    - CCPrompt: the interaction produced when a PromptRef is called.
    - bind(service_cls, **options): Provide the CCFabric tagged by the Service class.
    - NewSession: mints the id of a conversation that has not begun yet.
    - Session(*body, sid=None): brace that makes every prompt inside it one
      conversation, the one ``sid`` names when given.

A prompt outside a Session is one-shot, one ``claude`` process for one prompt.
Inside one under ``nu.arun`` it is a turn on the one process the brace holds
open; under ``nu.run`` it is still a process per prompt, on the brace's id.
Prefer ``nu.arun`` for real use so cc calls don't block the event loop
(streaming, UI ticks, parallel prompts all need it). Sync is fine for one-off
scripts.

Example::

    class Agent(nu.Service):
        ask = nustd.cc.PromptRef.method()

    app = nu.With(
        nustd.cc.bind(Agent, model="claude-sonnet-4-5", permission_mode="acceptEdits"),
        body=nu.print(nu.Dict(Agent.ask(prompt="write a haiku about rust"))["text"]),
    )

    asyncio.run(nu.arun(app))
"""

from __future__ import annotations

from .fabric import CCFabric
from .interactions import CCPrompt, NewSession
from .presets import bind
from .refs import PromptRef
from .session import Session, SessionHandle


__all__ = [
    "CCFabric",
    "CCPrompt",
    "NewSession",
    "PromptRef",
    "Session",
    "SessionHandle",
    "bind",
]
