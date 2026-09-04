"""Nu LLM fabric: OpenAI-compatible chat/completions, one wire, N providers.

Surface:
    - LLMFabric: httpx client for a chat/completions endpoint (base_url + api_key + model).
    - ChatRef: MethodRef for a chat endpoint on a Service.
    - Chat: the interaction produced when a ChatRef is called.
    - bind(service_cls, **kw): generic Provide.
    - ollama / openai / openrouter / groq / cerebras / xai / vllm: convenience presets.

Prefer `nu.arun` — LLM calls are network-bound and block the event loop under
sync. Sync is fine for one-off scripts.

Example (ollama on the red machine)::

    class Bot(nu.Service):
        chat = nu.llm.ChatRef.method(temperature=0.7)

    app = nu.With(
        nu.llm.ollama(Bot, host="red", model="qwen2.5:7b-instruct"),
        body=nu.print(nu.dict(Bot.chat(prompt="haiku about rust"))["text"]),
    )
    nu.run(app)
"""

from __future__ import annotations

from .fabric import LLMFabric
from .interactions import Chat
from .presets import bind, cerebras, groq, ollama, openai, openrouter, vllm, xai
from .refs import ChatRef


__all__ = [
    "Chat",
    "ChatRef",
    "LLMFabric",
    "bind",
    "cerebras",
    "groq",
    "ollama",
    "openai",
    "openrouter",
    "vllm",
    "xai",
]
