"""CCFabric: config template + one async call into claude-agent-sdk.

Holds the default ClaudeAgentOptions (model, cwd, tools, system prompt, ...) for a
bound Service. Per-call overrides merge on top. `aprompt` runs one query and
collects the assistant's final text + the ResultMessage metadata.
"""

from __future__ import annotations

from dataclasses import fields, replace
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["CCFabric"]


class CCFabric:
    """Holds a ClaudeAgentOptions template. One query per prompt call."""

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

    def _merge(self, overrides: dict[str, object]) -> ClaudeAgentOptions:
        if not overrides:
            return self.options
        allowed = {f.name for f in fields(self.options)}
        clean = {k: v for k, v in overrides.items() if k in allowed and v is not None}
        return replace(self.options, **clean) if clean else self.options

    async def aprompt(self, prompt: str, **overrides: object) -> dict[str, Any]:
        """Run one prompt turn. Returns {text, session_id, total_cost_usd, duration_ms, num_turns}."""
        opts = self._merge(overrides)
        text_parts: list[str] = []
        meta: dict[str, Any] = {}
        async for msg in query(prompt=prompt, options=opts):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
            elif isinstance(msg, ResultMessage):
                meta = {
                    "session_id": getattr(msg, "session_id", None),
                    "total_cost_usd": getattr(msg, "total_cost_usd", None),
                    "duration_ms": getattr(msg, "duration_ms", None),
                    "num_turns": getattr(msg, "num_turns", None),
                    "result": getattr(msg, "result", None),
                }
        return {"text": meta.get("result") or "".join(text_parts), **meta}
