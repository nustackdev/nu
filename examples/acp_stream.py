"""ACP fabric, streamed: watch a Prompt Turn as it happens, tool calls and all.

Every Session Update prints as it lands, then the stop reason. The bind
answers permission requests with the agent's allow-once option, so the turn
runs unattended. Requires the `acp` extra, Node and a Claude login.

    python examples/acp_stream.py
"""

import asyncio
import tempfile

import nu
import nustd


Claude = nustd.acp.AgentRef("claude")


@nu.host
def line(item: dict) -> str:
    kind = item.get("session_update")
    if kind == "agent_message_chunk":
        return item["content"].get("text", "")
    if kind == "tool_call":
        return f"  > {item.get('kind', 'other')}: {item['title']}"
    if kind == "tool_call_update" and item.get("status"):
        return f"  < {item['tool_call_id']} {item['status']}"
    if kind == "usage_update":
        return f"  [{item['used']:,} / {item['size']:,} tokens]"
    if "stop_reason" in item:
        return f"done: {item['stop_reason']}"
    return f"  [{kind}]"


app = nu.With(
    nustd.acp.claude(Claude, cwd=tempfile.mkdtemp(), permissions="allow_once"),
    body=nu.let(
        nu.Dict(Claude.new_session())["session_id"],
        lambda sid: nu.ForEachDo(
            Claude[sid].prompt("write hello.txt saying hi, then list the directory"),
            lambda item: nu.print(line(item)),
        ),
    ),
)

if __name__ == "__main__":
    asyncio.run(nu.arun(app))
