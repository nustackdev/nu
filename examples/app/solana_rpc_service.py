"""Solana JSON-RPC demo — Ref with method descriptors against mainnet.

Shows: Ref-based service access, method descriptors,
typed returns, lazy term trees, live RPC calls.
"""

from __future__ import annotations

import asyncio

import httpx

from nu import Context, print_tree
from nu.abc import DictI, IntI, StrI, method
from nu.abc.morphisms import AtOp
from nu.abc.types import TypeBase
from nu.abc.values import Interface
from nu.core import Ref


# =============================================================================
# RPC CLIENT
# =============================================================================

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaClient:
    """Thin JSON-RPC client. __getattr__ dispatches any method name as an RPC call."""

    def __init__(self, url: str = MAINNET):
        self._url = url
        self._id = 0

    def __getattr__(self, name: str):
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
# TYPED RETURN — TransactionType / TransactionValue
# =============================================================================


class TransactionType(TypeBase[dict]):
    """Typed access to Solana getTransaction response fields."""

    @property
    def slot(self) -> IntI:
        return IntI(AtOp(self, "slot"))

    @property
    def block_time(self) -> IntI:
        return IntI(AtOp(self, "blockTime"))

    @property
    def fee(self) -> IntI:
        meta = DictI(AtOp(self, "meta"))
        return IntI(AtOp(meta, "fee"))

    @property
    def first_signature(self) -> StrI:
        tx = DictI(AtOp(self, "transaction"))
        sigs = DictI(AtOp(tx, "signatures"))
        return StrI(AtOp(sigs, 0))


class TransactionValue(Interface[dict], TransactionType):
    pass


# =============================================================================
# REF — context-resolved Solana client
# =============================================================================


class SolanaRef(Ref[SolanaClient]):
    """Ref that resolves a SolanaClient from context."""

    async def resolve(self, ctx: Context) -> str:
        return "solana"

    async def fetch(self, ctx: Context) -> SolanaClient:
        return ctx[SolanaClient]


class Solana(SolanaRef):
    """Solana service with typed method descriptors."""

    get_slot = method(IntI, "getSlot")
    get_block = method(DictI, "getBlock")
    get_transaction = method(TransactionValue, "getTransaction")
    get_latest_blockhash = method(DictI, "getLatestBlockhash")
    get_balance = method(DictI, "getBalance")


# =============================================================================
# DEMO
# =============================================================================


async def main():
    client = SolanaClient()

    # Bind: service client → context
    ctx = Context().bind(client, SolanaClient)

    # --- print term trees ---
    print("get_slot() tree:")
    print_tree(Solana.get_slot())
    print()

    print("get_balance(pubkey) tree:")
    print_tree(Solana.get_balance("So11111111111111111111111111111111111111112"))
    print()

    # --- basic calls (class-level access) ---
    slot = await Solana.get_slot().execute(ctx)
    print(f"Current slot: {slot}")

    bh = await Solana.get_latest_blockhash().execute(ctx)
    print(f"Latest blockhash: {bh['value']['blockhash']}")


if __name__ == "__main__":
    asyncio.run(main())
