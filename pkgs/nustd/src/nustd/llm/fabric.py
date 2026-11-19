"""LLMFabric: httpx client aimed at an OpenAI-compatible /v1/chat/completions endpoint.

Holds base_url + api_key + default model, plus request-body defaults every call
inherits. One fabric = one endpoint. Presets (ollama, openai, openrouter, ...)
just fill base_url and api_key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["LLMFabric"]


class LLMFabric:
    """One OpenAI-compatible endpoint: its config and its sync + async clients.

    Holds no request logic; the interactions build the body, send it through
    ``client`` / ``aclient`` and read the reply.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        model: str = "",
        timeout: float = 120.0,
        headers: dict[str, str] | None = None,
        defaults: dict[str, object] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.headers = dict(headers or {})
        self.defaults = dict(defaults or {})
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

    @property
    def client(self) -> httpx.Client:
        """The opened sync client. Raises outside a sync run of the bracket."""
        if self._sync is None:
            msg = "LLMFabric sync client not opened; run under nu.run inside the preset"
            raise RuntimeError(msg)
        return self._sync

    @property
    def aclient(self) -> httpx.AsyncClient:
        """The opened async client. Raises outside an async run of the bracket."""
        if self._async is None:
            msg = "LLMFabric async client not opened; run under nu.arun inside the preset"
            raise RuntimeError(msg)
        return self._async
