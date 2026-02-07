"""eb_service demo — Solana JSON-RPC against mainnet.

Shows: method descriptors, typed returns via custom Type/Value, live RPC calls.
"""

from __future__ import annotations

import asyncio

import httpx

from eb_service import Interface, method
from everybase import Context
from everybase.abc import DictValue, IntValue, StrValue
from everybase.abc.morphisms import AtOp
from everybase.abc.types import TypeBase
from everybase.abc.values import ValueBase


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
# INTERFACE
# =============================================================================


class Solana(Interface):
    _service_type = SolanaClient

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
    ctx = Context().with_handle(SolanaClient, client)
    sol = Solana()

    # --- basic calls ---
    slot = await sol.get_slot().execute(ctx)
    print(f"Current slot: {slot}")

    bh = await sol.get_latest_blockhash().execute(ctx)
    print(f"Latest blockhash: {bh['value']['blockhash']}")

    pubkey = "So11111111111111111111111111111111111111112"
    balance = await sol.get_balance(pubkey).execute(ctx)
    print(f"Balance: {balance['value'] / 1e9:.4f} SOL")

    # --- get a recent block to find a transaction ---
    block = await sol.get_block(
        slot - 5,
        {"encoding": "json", "transactionDetails": "signatures", "rewards": False},
    ).execute(ctx)
    sig = block["signatures"][0]
    print(f"\nRecent block {slot - 5}: {len(block['signatures'])} txns")

    # --- typed return: TransactionValue ---
    # tx is a lazy term — field access composes BEFORE execution
    tx = sol.get_transaction(sig, {"encoding": "json"})
    tx_slot = await tx.slot.execute(ctx)
    tx_fee = await tx.fee.execute(ctx)
    print(f"\nTransaction {sig[:20]}...:")
    print(f"  slot: {tx_slot}")
    print(f"  fee:  {tx_fee} lamports")

    # lazy composition: fee_term is a pure expression tree, no RPC until execute()
    fee_term = tx.fee
    print(f"\nLazy term: {fee_term!r}")


if __name__ == "__main__":
    asyncio.run(main())
