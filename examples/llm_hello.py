"""Hit ollama on the red machine via nustd.llm: one whole reply, one chat, one stream.

Prereq: ollama up on red with qwen2.5:7b-instruct pulled, reachable at
`http://red:11434` from the mac (add `red` to /etc/hosts or use its IP).

    python examples/llm_hello.py
"""

import nu
import nustd


llm = nustd.llm.LLMRef()


def show(label, r):
    return nu.print(nu.str(label) + ": " + nu.str(nu.dict(r)["text"]))


app = nustd.llm.ollama(
    host="red",
    model="qwen2.5:7b-instruct",
    temperature=0.7,
    body=show("haiku", llm.chat(prompt="write a 3-line haiku about rust programming"))
    | show(
        "chat",
        llm.chat(
            messages=[
                {"role": "system", "content": "reply in exactly one word."},
                {"role": "user", "content": "colour of the sky?"},
            ],
        ),
    )
    | nu.print(nu.str("").join(nu.Collect(llm.chat_stream(prompt="count to five")))),
)

nu.run(app)
