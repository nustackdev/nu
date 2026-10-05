"""CCFabric: config template + the calls into claude-agent-sdk.

Holds the default ClaudeAgentOptions (model, cwd, tools, system prompt, ...) for a
bound Service. Per-call overrides merge on top. A prompt either runs one-shot,
one ``claude`` process for the one prompt, or as a turn on a client a Session
holds open. Both drain the stream the same way and hand back the same dict.
"""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    get_session_info,
    query,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from nu.lang.runtime import Context


__all__ = ["CCFabric"]


class CCFabric:
    """Holds a ClaudeAgentOptions template and makes every call into the SDK."""

    def __init__(self, *, options: ClaudeAgentOptions | None = None, **defaults: object) -> None:
        self.options = options or ClaudeAgentOptions(**defaults)  # type: ignore[arg-type]

    def setup(self, ctx: Context) -> None:  # noqa: D102
        pass

    def cleanup(self) -> None:  # noqa: D102
        pass

    async def asetup(self, ctx: Context) -> None:  # noqa: D102
        pass

    async def acleanup(self) -> None:  # noqa: D102
        pass

    def options_for(self, overrides: dict[str, object]) -> ClaudeAgentOptions:
        """The bound options with one call's overrides on top. Unknown keys are dropped."""
        if not overrides:
            return self.options
        allowed = {f.name for f in fields(self.options)}
        clean = {k: v for k, v in overrides.items() if k in allowed and v is not None}
        return replace(self.options, **clean) if clean else self.options

    async def aprompt(
        self, prompt: str, *, sid: str | None = None, **overrides: object
    ) -> dict[str, Any]:
        """Run one prompt in a ``claude`` process of its own, under ``sid`` when given.

        Returns {text, session_id, total_cost_usd, duration_ms, num_turns, result}.
        """
        options = continuing(self.options_for(overrides), sid)
        return await collected(query(prompt=prompt, options=options))

    async def aconnect(self, options: ClaudeAgentOptions, sid: str | None) -> ClaudeSDKClient:
        """Start one ``claude`` process that later turns talk through, under ``sid`` when given."""
        client = ClaudeSDKClient(options=continuing(options, sid))
        await client.connect()
        return client

    async def aturn(self, client: ClaudeSDKClient, prompt: str) -> dict[str, Any]:
        """Send one prompt on an open client and drain its reply. Same dict as ``aprompt``."""
        await client.query(prompt)
        return await collected(client.receive_response())


def continuing(options: ClaudeAgentOptions, sid: str | None) -> ClaudeAgentOptions:
    """``options`` set to run under the conversation ``sid``.

    The CLI takes a chosen id two ways and refuses the wrong one: ``--resume``
    for a conversation that has a transcript, ``--session-id`` to begin one
    under an id nothing has used. So the transcript decides, looked up where
    the CLI keeps it for this working directory. Without a sid the options are
    left alone and the CLI picks a fresh id.
    """
    if sid is None:
        return options
    held = get_session_info(sid, directory=str(options.cwd or Path.cwd()))
    if held is None:
        return replace(options, session_id=sid, resume=None)
    return replace(options, resume=sid, session_id=None)


async def collected(messages: AsyncIterator[Any]) -> dict[str, Any]:
    """Drain one reply: the assistant's text, then the result's accounting.

    The SDK's final result string wins over the concatenated text blocks. A
    stream that ends without a result message carries no accounting keys.
    """
    text_parts: list[str] = []
    meta: dict[str, Any] = {}
    async for msg in messages:
        if isinstance(msg, AssistantMessage):
            text_parts.extend(block.text for block in msg.content if isinstance(block, TextBlock))
        elif isinstance(msg, ResultMessage):
            meta = {
                "session_id": getattr(msg, "session_id", None),
                "total_cost_usd": getattr(msg, "total_cost_usd", None),
                "duration_ms": getattr(msg, "duration_ms", None),
                "num_turns": getattr(msg, "num_turns", None),
                "result": getattr(msg, "result", None),
            }
    return {"text": meta.get("result") or "".join(text_parts), **meta}
