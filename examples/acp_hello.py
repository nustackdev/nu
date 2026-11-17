"""ACP fabric: one question to Claude Code, the answer printed when the turn ends.

A Prompt Turn streams Session Updates; the answer is the text of its
``agent_message_chunk`` items. Requires the `acp` extra, Node (the adapter
runs through `npx`) and a Claude login on the machine. The agent only
answers, so any permission it asks for is rejected.

    python examples/acp_hello.py
"""

import asyncio
import tempfile

import nu
import nustd


Claude = nustd.acp.AgentRef("claude")


@nu.host
def answer(items: list) -> str:
    return "".join(
        item["content"].get("text", "")
        for item in items
        if item.get("session_update") == "agent_message_chunk"
    )


app = nu.With(
    nustd.acp.claude(Claude, cwd=tempfile.mkdtemp(), permissions="reject_once"),
    body=nu.let(
        nu.Dict(Claude.new_session())["session_id"],
        lambda sid: nu.print(answer(nu.Collect(Claude[sid].prompt("write a haiku about rust")))),
    ),
)

if __name__ == "__main__":
    asyncio.run(nu.arun(app))
