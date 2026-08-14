"""Claude Code fabric: ask cc for a haiku, print it.

Requires the `cc` extra (`claude-agent-sdk`) and the `claude` CLI on PATH.

    python examples/cc_haiku.py
"""

import nu


class Agent(nu.Service):
    ask = nu.cc.PromptRef.method()


app = nu.With(
    nu.cc.bind(Agent, permission_mode="bypassPermissions", max_turns=1),
    body=nu.print(nu.Dict(Agent.ask(prompt="write a 3-line haiku about rocksdb"))["text"]),
)

nu.run(app)
