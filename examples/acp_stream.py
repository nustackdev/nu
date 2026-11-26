"""ACP fabric, streamed: watch a Prompt Turn as it happens, tool calls and all.

The agent's text prints as it streams, each tool call once as it starts and
once as it ends, then the stop reason. The bind answers permission requests
with the agent's allow-once option, so the turn runs unattended. Requires the
`acp` extra, Node and a Claude login.

    python examples/acp_stream.py
"""

import asyncio
import tempfile

import nu
import nustd


Claude = nustd.acp.AgentRef("claude")


@nu.host
def piece(item: dict) -> str:
    kind = item.get("session_update")
    if kind == "agent_message_chunk":
        return item["content"].get("text", "")
    if kind == "tool_call":
        return f"\n  > {item.get('kind', 'other')}: {item['title']}\n"
    if kind == "tool_call_update" and item.get("status") in ("completed", "failed"):
        return f"  < {item['status']}\n"
    if "stop_reason" in item:
        return f"\ndone: {item['stop_reason']}\n"
    return ""


app = nu.With(
    nustd.acp.claude(Claude, cwd=tempfile.mkdtemp(), permissions="allow_once"),
    body=nu.let(
        lambda sid: nu.ForEachDo(
            Claude[sid].prompt("write hello.txt saying hi, then list the directory"),
            lambda item: nu.print(piece(item), end="", flush=True),
        ),
        sid=nu.Dict(Claude.new_session())["session_id"],
    ),
)

if __name__ == "__main__":
    asyncio.run(nu.arun(app))
