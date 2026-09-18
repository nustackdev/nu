"""HttpFabric: httpx client holder, sync + async."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx


if TYPE_CHECKING:
    from nu.lang.runtime import Context

__all__ = ["HttpFabric"]


class HttpFabric:
    """Holds a sync httpx.Client and an async httpx.AsyncClient.

    Bound on ctx via Provide. Sync client opens on `setup`, async on `asetup`.
    """

    def __init__(
        self,
        *,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url
        self.headers = dict(headers or {})
        self.timeout = timeout
        self._sync: httpx.Client | None = None
        self._async: httpx.AsyncClient | None = None

    def setup(self, ctx: Context) -> None:
        """Open the sync httpx.Client."""
        self._sync = httpx.Client(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    def cleanup(self) -> None:
        """Close the sync client."""
        if self._sync is not None:
            self._sync.close()
            self._sync = None

    async def asetup(self, ctx: Context) -> None:
        """Open the async httpx.AsyncClient."""
        self._async = httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    async def acleanup(self) -> None:
        """Close the async client."""
        if self._async is not None:
            await self._async.aclose()
            self._async = None

    def request(self, verb: str, path: str, **kwargs: object) -> object:
        """Sync request; raises on non-2xx; returns parsed JSON."""
        if self._sync is None:
            msg = "HttpFabric sync client not opened; run under nu.run inside With(...)"
            raise RuntimeError(msg)
        r = self._sync.request(verb, path, **kwargs)
        r.raise_for_status()
        return r.json()

    async def arequest(self, verb: str, path: str, **kwargs: object) -> object:
        """Async request; raises on non-2xx; returns parsed JSON."""
        if self._async is None:
            msg = "HttpFabric async client not opened; run under nu.arun inside With(...)"
            raise RuntimeError(msg)
        r = await self._async.request(verb, path, **kwargs)
        r.raise_for_status()
        return r.json()
