"""Solana JSON-RPC demo — Ref with method descriptors against mainnet.

Shows: Ref-based service access, method descriptors,
typed returns, lazy term trees, live RPC calls.
"""

from __future__ import annotations

import asyncio

import httpx

from everybase import Context, print_tree
from everybase.abc import DictValue, IntValue, StrValue, method
from everybase.abc.morphisms import AtOp
from everybase.abc.types import TypeBase
from everybase.abc.values import ValueBase
from everybase.core import Ref


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
    def slot(self) -> IntValue:
        return IntValue(AtOp(self, "slot"))

    @property
    def block_time(self) -> IntValue:
        return IntValue(AtOp(self, "blockTime"))

    @property
    def fee(self) -> IntValue:
        meta = DictValue(AtOp(self, "meta"))
        return IntValue(AtOp(meta, "fee"))

    @property
    def first_signature(self) -> StrValue:
        tx = DictValue(AtOp(self, "transaction"))
        sigs = DictValue(AtOp(tx, "signatures"))
        return StrValue(AtOp(sigs, 0))


class TransactionValue(ValueBase[dict], TransactionType):
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

    get_slot = method(IntValue, "getSlot")
    get_block = method(DictValue, "getBlock")
    get_transaction = method(TransactionValue, "getTransaction")
    get_latest_blockhash = method(DictValue, "getLatestBlockhash")
    get_balance = method(DictValue, "getBalance")


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
