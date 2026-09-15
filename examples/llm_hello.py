"""Hit ollama on the red machine via nustd.llm.

Prereq: ollama up on red with qwen2.5:7b-instruct pulled, reachable at
`http://red:11434` from the mac (add `red` to /etc/hosts or use its IP).

    python examples/llm_hello.py
"""

import nu
import nustd


class Bot(nu.Service):
    chat = nustd.llm.ChatRef.method(temperature=0.7)


def show(label, r):
    return nu.print(nu.str(label) + ": " + nu.str(nu.dict(r)["text"]))


app = nu.With(
    nustd.llm.ollama(Bot, host="red", model="qwen2.5:7b-instruct"),
    body=show("haiku", Bot.chat(prompt="write a 3-line haiku about rust programming"))
    | show(
        "chat",
        Bot.chat(
            messages=[
                {"role": "system", "content": "reply in exactly one word."},
                {"role": "user", "content": "colour of the sky?"},
            ],
        ),
    ),
)

nu.run(app)
