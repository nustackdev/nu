"""Claude Code fabric, streamed: watch a turn as it happens, tool calls and all.

A StreamRef call yields one event per thing the agent does: its text, each
tool it calls and what that gave back, then the result with the run's cost.
Requires the `cc` extra (`claude-agent-sdk`) and the `claude` CLI on PATH.

    python examples/cc_stream.py
"""

import asyncio
import tempfile

import nu
import nustd


class Agent(nu.Service):
    say = nustd.cc.StreamRef.method()


@nu.host
def line(ev: dict) -> str:
    kind = ev["type"]
    if kind == "text":
        return ev["text"]
    if kind == "tool_use":
        return f"  > {ev['name']} {ev['input']}"
    if kind == "tool_result":
        return f"  < {ev['content'][:80]!r}"
    if kind == "result":
        return f"done: {ev['num_turns']} turns, ${ev['total_cost_usd']:.4f}, {ev['duration_ms'] / 1000:.1f}s"
    return f"[{kind}]"


app = nu.With(
    nustd.cc.bind(
        Agent, model="claude-sonnet-5", cwd=tempfile.mkdtemp(), permission_mode="acceptEdits"
    ),
    body=nu.ForEachDo(
        Agent.say("in the current directory, write hello.txt saying hi, then list it"),
        lambda ev: nu.print(line(ev)),
    ),
)

if __name__ == "__main__":
    asyncio.run(nu.arun(app))
