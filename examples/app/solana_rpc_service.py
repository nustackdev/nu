"""Solana JSON-RPC demo -- a fabric called from inside the Nu tree.

Shows the in-tree fabric dispatch surface:

- ``SolanaClient`` is a bare-Python JSON-RPC client, bound on the Context via
  ``ctx.bind(SolanaClient, client)``.
- ``Solana`` is a ``FabricRef`` subclass naming that fabric (one Ref per bound
  fabric), with each RPC method declared as a ``method_query`` descriptor.
- ``Solana.slot()`` builds a dispatch atom that resolves the client from the
  Context at run time and calls ``getSlot`` -- the RPC now happens *inside* the
  tree, and its yield is a typed Form that composes like any query.

The methods are ``async def`` on the client (they await ``httpx``), so the tree
runs under ``arun``; the async path awaits the call. Two calls to ``Solana``
serialize (a WRITE on the one Solana fabric); against a different fabric they
would stay independent.
"""

from __future__ import annotations

import asyncio

import httpx

import nu


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
# SERVICE INTERFACE
# =============================================================================


class Solana(nu.FabricRef):
    """The SolanaClient as a Nu fabric: one Ref, methods declared inline."""

    fabric = SolanaClient

    slot = nu.method_query(nu.Int, "getSlot")
    block_height = nu.method_query(nu.Int, "getBlockHeight")


# =============================================================================
# DEMO
# =============================================================================


report = nu.Sequential(
    nu.print("Current slot:", Solana.slot()),
    nu.print("Block height:", Solana.block_height()),
)


async def main() -> None:
    ctx = nu.Context().bind(SolanaClient, SolanaClient())
    await nu.arun(report, ctx)


if __name__ == "__main__":
    asyncio.run(main())
