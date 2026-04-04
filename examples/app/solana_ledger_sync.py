#!/usr/bin/env python3
"""Solana ledger sync -- fetch blocks, persist transactions, resumable archive.

Single-process example: connects to Solana mainnet via JSON-RPC, fetches
confirmed blocks in a slot range, parses and persists transactions to
RocksDB. Resumable: skips already-synced slots on restart.

Demonstrates:
  Shapes        -- Transaction, Ledger (persistent data topology)
  Ref + method  -- typed, lazy RPC access via method descriptors
  Compositions  -- Seq, If, ForRange, Retry, TryCatch, Log
  Spans         -- ebv.Transaction (atomic writes)
  Deformations  -- inline_refs (tree rewrites before execution)
  Context       -- storage + service binding

Usage:
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 100
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 500 \\
        --program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

import aiohttp
from virtuals.tkv.storage import StorageProtocol

import nu.ops as ops
import nu_dict as ed
import nu_virtuals as ebv
from nu import Context, IntAttrRef, Nu, Ref
from nu.flows import ForRange, If, Log, Retry, Seq, TryCatch
from nu.interfaces import IntI, ListI
from nu.method import method
from nu.shapes import Shape
from nu_virtuals.presets import rocksdb_storage_inmemory


# =============================================================================
# Exceptions
# =============================================================================


class RpcError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"RPC error {code}: {message}")


class DroppedSlotError(Exception):
    """Slot was skipped or not available on chain."""

    def __init__(self, slot: int) -> None:
        self.slot = slot
        super().__init__(f"dropped slot {slot}")


# =============================================================================
# RPC client (minimal, correct)
# =============================================================================

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaRpc:
    """Minimal async Solana JSON-RPC client.

    No batching, no rate limiting, no retry logic.
    For production use a provider endpoint (Helius, Triton, etc).
    """

    def __init__(
        self,
        endpoint: str = MAINNET,
        timeout: float = 30.0,
        program_filter: str | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout
        self._program_filter = program_filter
        self._session: aiohttp.ClientSession | None = None
        self._id = 0

    async def connect(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                connector=aiohttp.TCPConnector(ssl=False),
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _ensure_connected(self) -> None:
        if self._session is None or self._session.closed:
            await self.connect()

    async def _call(self, method: str, params: list | None = None) -> Any:
        await self._ensure_connected()
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or []}
        async with self._session.post(
            self._endpoint, json=body, headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 429:
                raise RpcError(-429, "rate limited")
            resp.raise_for_status()
            data = await resp.json()
        if "error" in data:
            err = data["error"]
            raise RpcError(err.get("code", -1), err.get("message", ""))
        return data.get("result")

    # -- public API (resolved via ServiceRef method descriptors) ---------------

    async def get_slot(self) -> int:
        result = await self._call("getSlot", [{"commitment": "confirmed"}])
        return int(result)

    async def get_blocks(self, start: int, end: int) -> list[int]:
        result = await self._call("getBlocks", [start, end, {"commitment": "confirmed"}])
        return [int(s) for s in result]

    async def get_block(self, slot: int) -> list[dict]:
        """Fetch block, parse transactions into dicts matching Transaction shape.

        If program_filter is set, only includes txs touching that program.
        Raises DroppedSlotError for skipped/unavailable slots.
        """
        try:
            result = await self._call(
                "getBlock",
                [
                    slot,
                    {
                        "commitment": "confirmed",
                        "encoding": "json",
                        "transactionDetails": "full",
                        "rewards": False,
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            )
        except RpcError as e:
            if e.code in (-32009, -32007):
                raise DroppedSlotError(slot) from e
            raise
        if result is None:
            raise DroppedSlotError(slot)

        txs = _parse_block(slot, result)
        if self._program_filter:
            txs = [t for t in txs if _involves_program(t, self._program_filter)]
        return txs


# =============================================================================
# Block parsing
# =============================================================================


def _parse_block(slot: int, data: dict) -> list[dict]:
    """Parse raw block response into list of tx dicts matching Transaction shape."""
    block_time = data.get("blockTime", 0) or 0
    txs = []
    for i, raw in enumerate(data.get("transactions", [])):
        tx_data, meta = raw.get("transaction", {}), raw.get("meta", {})
        if not tx_data:
            continue
        msg = tx_data.get("message", {})

        # All account keys: static + loaded addresses (versioned txs)
        accounts = list(msg.get("accountKeys", []))
        for addr_type in ("writable", "readonly"):
            accounts.extend(meta.get("loadedAddresses", {}).get(addr_type, []))

        sigs = tx_data.get("signatures", [])
        err = meta.get("err")

        txs.append(
            {
                "signature": sigs[0] if sigs else "",
                "slot_number": slot,
                "block_time": block_time,
                "block_index": i,
                "fee": meta.get("fee", 0),
                "err": str(err) if err else "",
                "accounts": accounts,
                "instructions": _parse_ixs(msg.get("instructions", []), accounts),
                "inner_instructions": [
                    {
                        "index": s.get("index", 0),
                        "instructions": _parse_ixs(s.get("instructions", []), accounts),
                    }
                    for s in meta.get("innerInstructions", [])
                ],
                "pre_balances": meta.get("preBalances", []),
                "post_balances": meta.get("postBalances", []),
                "pre_token_balances": _parse_token_balances(meta.get("preTokenBalances")),
                "post_token_balances": _parse_token_balances(meta.get("postTokenBalances")),
                "logs": meta.get("logMessages", []),
                "compute_units": meta.get("computeUnitsConsumed", 0),
            }
        )
    return txs


def _parse_ixs(raw: list[dict], accounts: list[str]) -> list[dict]:
    """Parse instruction list, resolving account indices to addresses."""
    return [
        {
            "program_id": (
                accounts[ix.get("programIdIndex", 0)]
                if ix.get("programIdIndex", 0) < len(accounts)
                else ""
            ),
            "accounts": [accounts[j] for j in ix.get("accounts", []) if j < len(accounts)],
            "data": ix.get("data", ""),
        }
        for ix in raw
    ]


def _parse_token_balances(raw: list[dict] | None) -> list[dict]:
    """Parse token balance list from RPC response."""
    if not raw:
        return []
    return [
        {
            "account_index": tb.get("accountIndex", 0),
            "mint": tb.get("mint", ""),
            "owner": tb.get("owner", ""),
            "amount": tb.get("uiTokenAmount", {}).get("amount", "0"),
            "decimals": tb.get("uiTokenAmount", {}).get("decimals", 0),
        }
        for tb in raw
    ]


def _involves_program(tx: dict, program_id: str) -> bool:
    """Check if any instruction in the transaction targets the given program."""
    for ix in tx.get("instructions", []):
        if ix.get("program_id") == program_id:
            return True
    for inner in tx.get("inner_instructions", []):
        for ix in inner.get("instructions", []):
            if ix.get("program_id") == program_id:
                return True
    return False


# =============================================================================
# Service declaration
# =============================================================================


class SolanaRef(Ref[SolanaRpc]):
    """Ref that resolves a SolanaRpc from Context.

    method() descriptors create lazy terms that resolve the actual
    SolanaRpc at execution time.

    Bind:   ctx = ctx.bind(rpc, SolanaRpc)
    Use:    SolanaRef.get_slot()            -- returns a lazy term
            SolanaRef.get_block(slot_ref)   -- slot_ref can be a Ref or literal
    """

    async def resolve(self, ctx: Context) -> str:
        return "solana_rpc"

    async def fetch(self, ctx: Context) -> SolanaRpc:
        return ctx[SolanaRpc]

    get_slot = method(IntI, "get_slot")
    get_blocks = method(ListI, "get_blocks")
    get_block = method(ListI, "get_block")


# =============================================================================
# Shapes
# =============================================================================


class Transaction(Shape):
    """Single Solana transaction. All standard fields, stored as-is.

    Scalar fields are individually addressable. Lists (accounts, instructions,
    balances, logs) are primitive blobs -- stored and read whole.
    """

    # Metadata
    signature = ebv.StrRef.slot()
    slot_number = ebv.IntRef.slot()
    block_time = ebv.IntRef.slot()
    block_index = ebv.IntRef.slot()
    fee = ebv.IntRef.slot()
    err = ebv.StrRef.slot()  # empty = success

    # Structure (primitive blobs)
    accounts = ebv.PrimitiveListRef.slot()
    instructions = ebv.PrimitiveListRef.slot()
    inner_instructions = ebv.PrimitiveListRef.slot()

    # Balances (primitive blobs)
    pre_balances = ebv.PrimitiveListRef.slot()
    post_balances = ebv.PrimitiveListRef.slot()
    pre_token_balances = ebv.PrimitiveListRef.slot()
    post_token_balances = ebv.PrimitiveListRef.slot()

    # Extra
    logs = ebv.PrimitiveListRef.slot()
    compute_units = ebv.IntRef.slot()


TX_ID_MULTIPLIER = 10_000
"""Numeric tx ID = slot * 10_000 + block_index. Preserves block ordering."""


class Ledger(Shape):
    """Persistent transaction archive.

    tx_id = slot * 10_000 + block_index.
    Resumable via slots_synced.
    """

    txs = ebv.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = ebv.PrimitiveSetRef.slot()
    slots_dropped = ebv.PrimitiveSetRef.slot()
    current_slot = ebv.IntRef.slot()


# =============================================================================
# Scratch shapes (ephemeral, in-memory via nu_dict)
# =============================================================================


class _SlotScratch(Shape):
    """Per-slot scratch for sync_slot."""

    block_txs = ed.ListRef.slot(object)
    tx_id = ed.IntRef.slot()


class _RangeScratch(Shape):
    """Scratch for sync_range iteration."""

    slots = ed.ListRef.slot(int)
    slot_number = ed.IntRef.slot()


# =============================================================================
# Compositions
# =============================================================================


def sync_slot(ledger: type[Ledger], slot: int) -> Nu:
    """Fetch one block, parse txs, persist atomically. Skip if already synced.

    Handles dropped slots (skipped on-chain) gracefully.
    """
    sc = _SlotScratch
    tx_idx = IntAttrRef("tx_idx").get()

    return If(
        ops.Contains(ledger.slots_synced, slot).not_(),
        Retry(
            TryCatch(
                Seq(
                    sc.block_txs.store(SolanaRef.get_block(slot)),
                    Log("slot", slot, ":", ops.Len(sc.block_txs), "txs"),
                    ebv.Transaction(
                        ForRange(
                            0,
                            ops.Len(sc.block_txs),
                            Seq(
                                sc.tx_id.store(slot * TX_ID_MULTIPLIER + tx_idx),
                                ledger.txs[sc.tx_id].store(sc.block_txs[tx_idx]),
                            ),
                            index="tx_idx",
                        ),
                        ledger.slots_synced.add(slot),
                    ),
                ),
                catch=Seq(
                    ebv.Transaction(ledger.slots_dropped.add(slot)),
                    Log("dropped slot", slot),
                ),
                errors=DroppedSlotError,
            ),
            max_attempts=5,
            delay=1,
            backoff=1.5,
            on_attempt_fail=Log("retry slot", slot),
            on_fail=Log("giving up on slot", slot),
        ),
    )


def sync_range(ledger: type[Ledger], slot_from: int, slot_to: int) -> Nu:
    """Sync all confirmed slots in [slot_from, slot_to].

    Fetches the confirmed slot list via get_blocks(), then iterates each,
    delegating to sync_slot for fetch + parse + persist.
    """
    sc = _RangeScratch
    slot_idx = IntAttrRef("slot_idx").get()

    return Seq(
        sc.slots.store(SolanaRef.get_blocks(slot_from, slot_to)),
        Log("sync:", slot_from, "->", slot_to, "(", fn.Len(sc.slots), "confirmed)"),
        ForRange(
            0,
            fn.Len(sc.slots),
            Seq(
                sc.slot_number.store(sc.slots[slot_idx]),
                sync_slot(ledger, sc.slot_number),
            ),
            index="slot_idx",
        ),
        Log("sync complete"),
    )


# =============================================================================
# Main
# =============================================================================


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Solana ledger sync")
    p.add_argument("--slot-from", type=int, required=True, help="Start slot (inclusive)")
    p.add_argument("--slots", type=int, default=100, help="Number of slots to sync")
    p.add_argument("--endpoint", default=MAINNET, help="Solana RPC endpoint")
    p.add_argument("--program", default=None, help="Filter: only txs involving this program")
    p.add_argument("--db-path", default=".db-ledger", help="RocksDB storage path")
    return p.parse_args()


async def main() -> None:
    args = parse_args()

    rpc = SolanaRpc(endpoint=args.endpoint, program_filter=args.program)

    try:
        with rocksdb_storage_inmemory(args.db_path) as store:
            ctx = Context().bind(store, StorageProtocol).bind(rpc, SolanaRpc)

            slot_to = args.slot_from + args.slots

            # Build composition: init ledger state, then sync range
            init = ebv.Transaction(
                Seq(
                    If(Ledger.slots_synced.missing(), Ledger.slots_synced.store(set())),
                    If(Ledger.slots_dropped.missing(), Ledger.slots_dropped.store(set())),
                ),
            )
            tree = Seq(init, sync_range(Ledger, args.slot_from, slot_to))

            # Deformations: optimize before execution
            tree = ed.inline_refs(tree)
            tree = ebv.inline_refs(tree)

            print(f"syncing slots {args.slot_from} -> {slot_to}")
            print(f"endpoint: {args.endpoint}")
            if args.program:
                print(f"filter: program {args.program}")
            print(f"db: {args.db_path}\n")

            await tree.execute(ctx)
    finally:
        await rpc.close()


if __name__ == "__main__":
    asyncio.run(main())
