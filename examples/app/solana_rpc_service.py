"""Solana JSON-RPC demo -- service bound on the Context, called from the driver.

Shows: a bare-Python service (SolanaClient) bound on the Nu Context via
``ctx.bind(SolanaClient, client)``, exercised outside the tree, with results
funneled into a Nu tree via ``ctx.attrs``. The tree then reads those attrs
through the typed ``IntAttrRef`` / ``StrAttrRef`` surface and prints them.

FIXME: the old typed method-descriptor system (``method(IntI, "getSlot")``,
``TypeBase``/``Interface`` + ``AtOp``) is gone. Until a typed-RPC dispatch
surface returns, RPC calls happen outside the tree and their results are
funneled in as attrs.
"""

from __future__ import annotations

import asyncio

import httpx

from nu import Context, arun
from nu.context import IntAttrRef, StrAttrRef
from nu.core.io import print as nu_print
from nu.flows import Sequential


# =============================================================================
# RPC CLIENT
# =============================================================================

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaClient:
    """Thin JSON-RPC client. __getattr__ dispatches any method name as an RPC call."""

    def __init__(self, url: str = MAINNET) -> None:
        self._url = url
        self._id = 0

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        async def rpc_call(*params: object) -> object:
            self._id += 1
            payload = {"jsonrpc": "2.0", "id": self._id, "method": name, "params": list(params)}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self._url, json=payload)
                data = resp.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data["result"]

        return rpc_call


# =============================================================================
# DEMO
# =============================================================================


report = Sequential(
    nu_print("Current slot:", IntAttrRef("slot")),
    nu_print("Latest blockhash:", StrAttrRef("blockhash")),
)


async def main() -> None:
    client = SolanaClient()
    ctx = Context().bind(SolanaClient, client)

    # Drive the RPC calls outside the tree, then let the tree render the results.
    ctx.attrs["slot"] = int(await client.getSlot())
    bh = await client.getLatestBlockhash()
    ctx.attrs["blockhash"] = bh["value"]["blockhash"]

    await arun(report, ctx)


if __name__ == "__main__":
    asyncio.run(main())
