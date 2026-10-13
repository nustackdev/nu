"""CCFabric: config template + the calls into claude-agent-sdk.

Holds the default ClaudeAgentOptions (model, cwd, tools, system prompt, ...) for a
bound Service. Per-call overrides merge on top. A prompt either runs one-shot,
one ``claude`` process for the one prompt, or as a turn on a client a Session
holds open. Both drain the stream the same way and hand back the same dict.

A streamed prompt runs the same two ways but hands the reply over as it comes,
one plain dict per thing that happened (:func:`events_of` names them), the
last one the result with the run's accounting.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from contextlib import aclosing
from dataclasses import fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    get_session_info,
    query,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang.runtime import Context


__all__ = ["TRIM", "CCFabric", "bridged", "events", "events_of"]


#: Characters of a tool's output a ``tool_result`` event keeps. The rest is cut, and the cut said.
TRIM = 2000


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

    async def astream(
        self, prompt: str, *, sid: str | None = None, **overrides: object
    ) -> AsyncIterator[dict[str, Any]]:
        """``aprompt``, its reply handed over as it comes: one event per block, the result last."""
        options = continuing(self.options_for(overrides), sid)
        async with aclosing(events(query(prompt=prompt, options=options))) as stream:
            async for event in stream:
                yield event

    async def aturn_stream(
        self, client: ClaudeSDKClient, prompt: str
    ) -> AsyncIterator[dict[str, Any]]:
        """``aturn``, its reply handed over as it comes. Same events as ``astream``."""
        await client.query(prompt)
        async with aclosing(events(client.receive_response())) as stream:
            async for event in stream:
                yield event


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


async def events(messages: AsyncIterator[Any]) -> AsyncIterator[dict[str, Any]]:
    """One reply as events, in the order it happened (see :func:`events_of`).

    The result's ``text`` is the SDK's final result string, falling back to
    the reply's text blocks, the way :func:`collected` reads it.
    """
    said: list[str] = []
    async for msg in messages:
        for event in events_of(msg):
            if event["type"] == "text":
                said.append(event["text"])
            elif event["type"] == "result":
                event["text"] = event["text"] or "".join(said)
            yield event


def events_of(msg: object) -> list[dict[str, Any]]:
    """What one SDK message says, as plain dicts. Messages that say nothing a caller reads give none.

    - ``{"type": "init", session_id, model, cwd, tools}``: the process is up.
    - ``{"type": "text", text}``: a block of the assistant's text.
    - ``{"type": "delta", text}``: a piece of a text block still being written,
      only when the options ask for ``include_partial_messages``.
    - ``{"type": "thinking", text}``: a block of the assistant's thinking.
    - ``{"type": "tool_use", id, name, input}``: the assistant calls a tool.
    - ``{"type": "tool_result", id, content, is_error}``: what the tool gave
      back, as text, cut to :data:`TRIM` characters.
    - ``{"type": "result", text, session_id, total_cost_usd, duration_ms,
      num_turns, usage, is_error}``: the run is over, and what it cost.
    """
    if isinstance(msg, AssistantMessage):
        return [one for block in msg.content if (one := _block(block)) is not None]
    if isinstance(msg, UserMessage) and isinstance(msg.content, list):
        return [
            {
                "type": "tool_result",
                "id": block.tool_use_id,
                "content": _trimmed(block.content),
                "is_error": bool(block.is_error),
            }
            for block in msg.content
            if isinstance(block, ToolResultBlock)
        ]
    if isinstance(msg, SystemMessage) and msg.subtype == "init":
        data = msg.data or {}
        keys = ("session_id", "model", "cwd", "tools")
        return [{"type": "init", **{k: data.get(k) for k in keys}}]
    if isinstance(msg, StreamEvent):
        delta = msg.event.get("delta") or {}
        if msg.event.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
            return [{"type": "delta", "text": delta.get("text", "")}]
        return []
    if isinstance(msg, ResultMessage):
        return [
            {
                "type": "result",
                "text": msg.result or "",
                "session_id": msg.session_id,
                "total_cost_usd": msg.total_cost_usd,
                "duration_ms": msg.duration_ms,
                "num_turns": msg.num_turns,
                "usage": msg.usage or {},
                "is_error": bool(msg.is_error),
            }
        ]
    return []


def _block(block: object) -> dict[str, Any] | None:
    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    if isinstance(block, ThinkingBlock):
        return {"type": "thinking", "text": block.thinking}
    if isinstance(block, ToolUseBlock):
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return None


def _trimmed(content: object) -> str:
    """A tool result as text, cut to :data:`TRIM` characters."""
    if content is None:
        text = ""
    elif isinstance(content, str):
        text = content
    else:
        parts = []
        for part in content:  # type: ignore[attr-defined]
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
            elif isinstance(part, dict):
                parts.append(f"[{part.get('type', 'part')}]")
            else:
                parts.append(json.dumps(part, default=str))
        text = "\n".join(parts)
    if len(text) <= TRIM:
        return text
    return f"{text[:TRIM]}\n... {len(text) - TRIM:,} more characters"


def bridged(make: Callable[[], AsyncIterator[Any]]) -> Iterator[Any]:
    """The async stream ``make`` opens, pulled from sync code as it comes.

    The stream runs in one task on a loop of its own, in a thread, because the
    SDK holds task-bound scopes open across its items. Each item is handed
    over the moment it lands. Closing the iterator early cancels the stream
    and waits for it to wind down, so its ``claude`` process goes with it.
    """
    items: queue.Queue = queue.Queue()
    held: dict[str, Any] = {}
    up = threading.Event()

    async def pump() -> None:
        held["loop"], held["task"] = asyncio.get_running_loop(), asyncio.current_task()
        up.set()
        try:
            async with aclosing(make()) as stream:  # type: ignore[type-var]
                async for item in stream:
                    items.put(("item", item))
        except BaseException as exc:  # handed to the reader, raised there
            items.put(("error", exc))
            return
        items.put(("done", None))

    thread = threading.Thread(target=asyncio.run, args=(pump(),), name="nu-cc-stream", daemon=True)
    thread.start()
    try:
        while True:
            kind, value = items.get()
            if kind == "item":
                yield value
            elif kind == "error":
                raise value
            else:
                return
    finally:
        if thread.is_alive():
            up.wait()
            held["loop"].call_soon_threadsafe(held["task"].cancel)
            thread.join()
