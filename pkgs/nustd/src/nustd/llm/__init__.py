"""Nu LLM fabric: OpenAI-compatible chat/completions, one wire, N providers.

Surface:
    - LLMFabric: httpx client for a chat/completions endpoint (base_url + api_key + model).
    - LLMRef: the fabric ref; ``.chat(...)`` / ``.chat_stream(...)`` build on it.
    - Chat / ChatStream: one chat/completions call, whole or streamed.
    - endpoint(base_url, ...): the generic preset.
    - ollama / openai / openrouter / groq / cerebras / xai / vllm: convenience presets.

Prefer `nu.arun`: LLM calls are network-bound and block the event loop under
sync. Sync is fine for one-off scripts.

Example (ollama on the red machine)::

    llm = nustd.llm.LLMRef()

    app = nustd.llm.ollama(
        host="red",
        model="qwen2.5:7b-instruct",
        temperature=0.7,
        body=nu.print(nu.dict(llm.chat(prompt="haiku about rust"))["text"]),
    )
    nu.run(app)
"""

from __future__ import annotations

from .fabric import LLMFabric
from .interactions import Chat, ChatStream
from .presets import cerebras, endpoint, groq, ollama, openai, openrouter, vllm, xai
from .refs import LLMRef


__all__ = [
    "Chat",
    "ChatStream",
    "LLMFabric",
    "LLMRef",
    "cerebras",
    "endpoint",
    "groq",
    "ollama",
    "openai",
    "openrouter",
    "vllm",
    "xai",
]
