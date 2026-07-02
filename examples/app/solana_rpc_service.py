"""Solana JSON-RPC demo -- a service called from inside the Nu tree.

Shows the in-tree service dispatch surface:

- ``SolanaClient`` is a bare-Python JSON-RPC client, bound on the Context via
  ``ctx.bind(SolanaClient, client)``.
- ``Solana`` is a ``ServiceRef`` subclass naming that service (one fabric per
  service), with each RPC method declared as a ``method`` descriptor.
- ``Solana.slot()`` builds an ``InvokeAction`` that resolves the client from the
  Context at run time and calls ``getSlot`` -- the RPC now happens *inside* the
  tree, and its yield is a typed Form that composes like any query.

The methods are ``async def`` on the client (they await ``httpx``), so the tree
runs under ``arun``; the async path awaits the call. Two calls to ``Solana``
serialize (a WRITE on the one service fabric); against a different service they
would stay independent.
"""

from __future__ import annotations

import asyncio

import httpx

from nu import Context, IntForm, arun
from nu.context import ServiceRef, method_query
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
# SERVICE INTERFACE
# =============================================================================


class Solana(ServiceRef):
    """The SolanaClient as a Nu service: one fabric, methods declared inline."""

    service = SolanaClient

    slot = method_query(IntForm, "getSlot")
    block_height = method_query(IntForm, "getBlockHeight")


# =============================================================================
# DEMO
# =============================================================================


report = Sequential(
    nu_print("Current slot:", Solana.slot()),
    nu_print("Block height:", Solana.block_height()),
)


async def main() -> None:
    ctx = Context().bind(SolanaClient, SolanaClient())
    await arun(report, ctx)


if __name__ == "__main__":
    asyncio.run(main())
