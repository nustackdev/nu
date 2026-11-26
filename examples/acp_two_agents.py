"""ACP fabric, two agents: Claude Code and Codex answer one task side by side.

Each agent is its own process under its own name; one tree drives both in
parallel through the same interactions. Both only answer, so any
permission they ask for is rejected. Requires the `acp` extra, Node, and
Claude and Codex logins.

    python examples/acp_two_agents.py
"""

import asyncio
import tempfile

import nu
import nustd


Claude = nustd.acp.AgentRef("claude")
Codex = nustd.acp.AgentRef("codex")

TASK = "in two sentences: when is a write-once blob store the right choice?"


@nu.host
def answer(name: str, items: list) -> str:
    text = "".join(
        item["content"].get("text", "")
        for item in items
        if item.get("session_update") == "agent_message_chunk"
    )
    return f"{name}: {text}"


def draft(agent):
    return nu.let(
        lambda sid: nu.print(answer(agent.name, nu.Collect(agent[sid].prompt(TASK)))),
        sid=nu.Dict(agent.new_session())["session_id"],
    )


cwd = tempfile.mkdtemp()
app = nu.With(
    nustd.acp.claude(Claude, cwd=cwd, permissions="reject_once"),
    nustd.acp.codex(Codex, cwd=cwd, permissions="reject_once"),
    body=nu.ParallelAsync(draft(Claude), draft(Codex)),
)

if __name__ == "__main__":
    asyncio.run(nu.arun(app))
