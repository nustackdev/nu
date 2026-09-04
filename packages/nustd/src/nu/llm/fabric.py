"""LLMFabric: httpx client aimed at an OpenAI-compatible /v1/chat/completions endpoint.

Holds base_url + api_key + default model. One fabric = one endpoint. Presets
(ollama, openai, openrouter, ...) just fill those three.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["LLMFabric"]


class LLMFabric:
    """OpenAI-compat chat/completions client. Sync + async."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        model: str = "",
        timeout: float = 120.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.headers = dict(headers or {})
        if api_key:
            self.headers.setdefault("Authorization", f"Bearer {api_key}")
        self._sync: httpx.Client | None = None
        self._async: httpx.AsyncClient | None = None

    def setup(self, ctx: Context) -> None:  # noqa: D102
        self._sync = httpx.Client(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    def cleanup(self) -> None:  # noqa: D102
        if self._sync is not None:
            self._sync.close()
            self._sync = None

    async def asetup(self, ctx: Context) -> None:  # noqa: D102
        self._async = httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    async def acleanup(self) -> None:  # noqa: D102
        if self._async is not None:
            await self._async.aclose()
            self._async = None

    def _body(self, messages: list[dict], overrides: dict[str, object]) -> dict[str, Any]:
        body: dict[str, Any] = {"model": overrides.pop("model", None) or self.model}
        body["messages"] = messages
        for k, v in overrides.items():
            if v is not None:
                body[k] = v
        if not body["model"]:
            msg = "LLMFabric: no model set (pass `model=` on bind or on the call)"
            raise ValueError(msg)
        return body

    @staticmethod
    def _extract(data: dict) -> dict[str, Any]:
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        return {
            "text": message.get("content") or "",
            "message": message,
            "model": data.get("model"),
            "usage": data.get("usage"),
            "finish_reason": choice.get("finish_reason"),
        }

    def chat(self, messages: list[dict], **overrides: object) -> dict[str, Any]:
        """Sync one-shot chat completion."""
        if self._sync is None:
            msg = "LLMFabric sync client not opened; run under nu.run inside With(...)"
            raise RuntimeError(msg)
        r = self._sync.post("/v1/chat/completions", json=self._body(messages, overrides))
        r.raise_for_status()
        return self._extract(r.json())

    async def achat(self, messages: list[dict], **overrides: object) -> dict[str, Any]:
        """Async one-shot chat completion."""
        if self._async is None:
            msg = "LLMFabric async client not opened; run under nu.arun inside With(...)"
            raise RuntimeError(msg)
        r = await self._async.post("/v1/chat/completions", json=self._body(messages, overrides))
        r.raise_for_status()
        return self._extract(r.json())
