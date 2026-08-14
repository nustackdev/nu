"""Two independent cc sessions, two prompts each.

Each `nu.cc.Session(...)` scopes a fresh session across its body: the first prompt
starts a new cc session, the second continues it via `resume=session_id`. The two
Sessions do not see each other's context.

    python examples/cc_two_sessions.py
"""

import nu


class Agent(nu.Service):
    ask = nu.cc.PromptRef.method()


def show(label, r):
    return nu.print(nu.str(label) + ": " + nu.str(nu.dict(r)["text"]))


app = nu.With(
    nu.cc.bind(Agent, permission_mode="bypassPermissions", max_turns=1),
    body=nu.cc.Session(
        show("A1", Agent.ask(prompt="my favorite color is teal. remember it.")),
        show("A2", Agent.ask(prompt="what did i tell you my favorite color was? one word.")),
    )
    | nu.cc.Session(
        show("B1", Agent.ask(prompt="my favorite animal is an octopus. remember it.")),
        show("B2", Agent.ask(prompt="what did i tell you my favorite animal was? one word.")),
    ),
)

nu.run(app)
