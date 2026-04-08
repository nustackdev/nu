#!/usr/bin/env python3
"""Solana ledger sync -- fetch blocks, persist transactions, resumable archive.

Single-process example: connects to Solana mainnet via JSON-RPC, fetches
confirmed blocks in a slot range, parses and persists transactions to
RocksDB. Resumable: skips already-synced slots on restart.

Demonstrates:
  Shapes        -- Transaction, Ledger (persistent data topology)
  Ref + method  -- typed, lazy RPC access via method descriptors
  Compositions  -- | (sequential), If, ForEach, Retry, TryCatch, Log
  Spans         -- nu_virtuals.Transaction (atomic writes)
  Deformations  -- inline_refs (app rewrites before execution)
  Context       -- storage + service binding

Usage:
    python examples/solana_ledger_sync.py --slot-from 335000000 --slots 100
    python examples/solana_ledger_sync.py --slot-from 335000000 --slots 500 \\
        --program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
"""

from __future__ import annotations

import argparse
import logging

import aiohttp

import nu
import nu_debugger
import nu_dict
import nu_virtuals
from nu.context.attr_refs import AttrRef


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger("sol")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.propagate = False


class RpcError(Exception):
    def __init__(self, code, msg):
        self.code = code
        super().__init__(msg)


class DroppedSlotError(Exception):
    pass


# =============================================================================
# RPC client
# =============================================================================


class SolanaRpc:
    """Minimal async Solana JSON-RPC client."""

    def __init__(
        self, endpoint: str = "https://api.mainnet-beta.solana.com", timeout: float = 30.0
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None
        self._id = 0

    async def _call(self, method: str, params: list | None = None) -> object:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                connector=aiohttp.TCPConnector(ssl=False),
            )
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or []}
        async with self._session.post(self._endpoint, json=body) as resp:
            if resp.status == 429:
                raise RpcError(-429, "rate limited")
            resp.raise_for_status()
            data = await resp.json()
        if "error" in data:
            err = data["error"]
            raise RpcError(err.get("code", -1), err.get("message", ""))
        return data.get("result")

    async def get_slot(self) -> int:
        return int(await self._call("getSlot", [{"commitment": "confirmed"}]))

    async def get_blocks(self, start: int, end: int) -> list[int]:
        return [
            int(s) for s in await self._call("getBlocks", [start, end, {"commitment": "confirmed"}])
        ]

    async def get_block(self, slot: int) -> list[dict]:
        """Fetch block, return tx dicts matching Transaction shape."""
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

        block_time = result.get("blockTime", 0) or 0
        txs = []
        for i, raw in enumerate(result.get("transactions", [])):
            tx, meta = raw.get("transaction", {}), raw.get("meta", {})
            if not tx:
                continue
            msg = tx.get("message", {})

            # Resolve all program IDs (top-level + inner) for filtering
            accounts = list(msg.get("accountKeys", []))
            for t in ("writable", "readonly"):
                accounts.extend(meta.get("loadedAddresses", {}).get(t, []))
            programs = set()
            for ix in msg.get("instructions", []):
                idx = ix.get("programIdIndex", 0)
                if idx < len(accounts):
                    programs.add(accounts[idx])
            for inner in meta.get("innerInstructions", []):
                for ix in inner.get("instructions", []):
                    idx = ix.get("programIdIndex", 0)
                    if idx < len(accounts):
                        programs.add(accounts[idx])

            txs.append(
                {
                    "slot_number": slot,
                    "block_time": block_time,
                    "block_index": i,
                    "signatures": tx.get("signatures", []),
                    "account_keys": msg.get("accountKeys", []),
                    "instructions": msg.get("instructions", []),
                    "fee": meta.get("fee", 0),
                    "err": str(meta.get("err") or ""),
                    "compute_units": meta.get("computeUnitsConsumed", 0),
                    "programs": list(programs),
                    "pre_balances": meta.get("preBalances", []),
                    "post_balances": meta.get("postBalances", []),
                    "pre_token_balances": meta.get("preTokenBalances", []),
                    "post_token_balances": meta.get("postTokenBalances", []),
                    "loaded_addresses": meta.get("loadedAddresses", {}),
                    "inner_instructions": meta.get("innerInstructions", []),
                    "log_messages": meta.get("logMessages", []),
                }
            )
        return txs

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        await self.close()


# =============================================================================
# Service declaration
# =============================================================================


class SolanaRef(nu.Ref[SolanaRpc]):
    """Ref that resolves a SolanaRpc from Context.

    method() descriptors create lazy terms that resolve the actual
    SolanaRpc at execution time.

    Bind:   ctx = ctx.bind(rpc, SolanaRpc)
    Use:    SolanaRef.get_slot()            -- returns a lazy term
            SolanaRef.get_block(slot_ref)   -- slot_ref can be a Ref or literal
    """

    async def resolve(self, ctx: nu.Context) -> str:
        return "solana_rpc"

    async def fetch(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    get_slot = nu.method(nu.IntI, "get_slot")
    get_blocks = nu.method(nu.ListI, "get_blocks")
    get_block = nu.method(nu.ListI, "get_block")


# =============================================================================
# Shapes
# =============================================================================


class Transaction(nu.shapes.Shape):
    """Solana transaction. Mirrors RPC structure, no parsing."""

    slot_number = nu_virtuals.IntRef.slot()
    block_time = nu_virtuals.IntRef.slot()
    block_index = nu_virtuals.IntRef.slot()
    signatures = nu_virtuals.PrimitiveListRef.slot()
    account_keys = nu_virtuals.PrimitiveListRef.slot()
    instructions = nu_virtuals.PrimitiveListRef.slot()
    fee = nu_virtuals.IntRef.slot()
    err = nu_virtuals.StrRef.slot()
    compute_units = nu_virtuals.IntRef.slot()
    programs = nu_virtuals.PrimitiveListRef.slot()
    pre_balances = nu_virtuals.PrimitiveListRef.slot()
    post_balances = nu_virtuals.PrimitiveListRef.slot()
    pre_token_balances = nu_virtuals.PrimitiveListRef.slot()
    post_token_balances = nu_virtuals.PrimitiveListRef.slot()
    loaded_addresses = nu_virtuals.PrimitiveDictRef.slot()
    # Primitive blobs - verbose, read in bulk
    inner_instructions = nu_virtuals.PrimitiveListRef.slot()
    log_messages = nu_virtuals.PrimitiveListRef.slot()


TX_ID_MULTIPLIER = 10_000
"""Numeric tx ID = slot * 10_000 + block_index. Preserves block ordering."""


class BlockMeta(nu.shapes.Shape):
    """Block meta."""

    skipped = nu_virtuals.IntRef.slot()
    synced = nu_virtuals.IntRef.slot()


class Ledger(nu.shapes.Shape):
    """Persistent transaction archive.

    tx_id = slot * 10_000 + block_index.
    Resumable via slots_synced.
    """

    txs = nu_virtuals.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = nu_virtuals.PrimitiveSetRef.slot()
    slots_dropped = nu_virtuals.PrimitiveSetRef.slot()
    current_slot = nu_virtuals.IntRef.slot()
    blocks_meta = nu_virtuals.ShapesDictRef.slot(BlockMeta, key_type=int)


# =============================================================================
# Scratch shapes (ephemeral, in-memory via nu_dict)
# =============================================================================


class _SlotScratch(nu.shapes.Shape):
    """Per-slot scratch for sync_slot."""

    tx_id = nu_dict.IntRef.slot()


class _RangeScratch(nu.shapes.Shape):
    """Scratch for sync_range iteration."""

    slots = nu_dict.ListRef.slot(int)


# =============================================================================
# Compositions
# =============================================================================


def _involves_program(program_id: nu.StrArg) -> nu.Nu:
    """Does ctx.attrs["tx"] involve the given program?"""
    return nu.ops.Contains(nu.AnyI(nu.AtOp(nu.AnyAttrRef("tx"), "programs")), program_id)


def _persist_tx(ledger: type[Ledger], slot: nu.IntArg) -> nu.Nu:
    """Persist one tx from ctx.attrs["tx"] to ledger."""
    return _SlotScratch.tx_id.store(
        nu.IntI(slot) * TX_ID_MULTIPLIER + nu.AtOp(nu.AttrRef("tx"), "block_index")
    ) | ledger.txs[_SlotScratch.tx_id].store(nu.AnyAttrRef("tx"))


def sync_slot(ledger: type[Ledger], slot: nu.IntArg, *, program_id: nu.StrArg = "") -> nu.Nu:
    """Fetch one block, iterate txs, persist per-tx. Skip if already synced."""
    return nu.If(
        nu.ops.Contains(ledger.slots_synced, slot).not_(),
        nu.Retry(
            nu.TryCatch(
                nu_virtuals.Transaction(
                    ledger.blocks_meta[slot].skipped.init(0),
                    ledger.blocks_meta[slot].synced.init(0),
                )
                | nu_virtuals.Transaction(
                    nu.ForEach(
                        SolanaRef.get_block(slot),
                        nu.If(
                            nu.ops.ToBool(program_id),
                            nu.If(
                                _involves_program(program_id),
                                ledger.blocks_meta[slot].synced.inc()
                                | _persist_tx(ledger, slot)
                                | nu.If(
                                    (ledger.blocks_meta[slot].synced % 10).eq(0),
                                    nu.Log("synced:", ledger.blocks_meta[slot].synced),
                                ),
                                ledger.blocks_meta[slot].skipped.inc()
                                | nu.If(
                                    (ledger.blocks_meta[slot].skipped % 50).eq(0),
                                    nu.Log("skipped:", ledger.blocks_meta[slot].skipped),
                                ),
                            ),
                            _persist_tx(ledger, slot)
                            | ledger.blocks_meta[slot].synced.inc()
                            | nu.If(
                                (ledger.blocks_meta[slot].synced % 10).eq(0),
                                nu.Log("synced:", ledger.blocks_meta[slot].synced),
                            ),
                        ),
                        item="tx",
                    ),
                ),
                catch=(
                    nu_virtuals.Transaction(ledger.slots_dropped.add(slot))
                    | nu.Log("dropped slot", slot)
                ),
                errors=DroppedSlotError,
            ),
            max_attempts=5,
            delay=1,
            backoff=1.5,
            on_attempt_fail=nu.Log("retry slot", slot),
            on_fail=nu.Log("giving up on slot", slot),
        ),
        nu.Log("txs: ", ledger.current_slot),
    )


def sync_range(
    ledger: type[Ledger], slot_from: int, slot_to: int, *, program_id: nu.StrArg = ""
) -> nu.Nu:
    """Sync all confirmed slots in [slot_from, slot_to].

    Fetches the confirmed slot list via get_blocks(), then iterates each,
    delegating to sync_slot for fetch + persist.
    """

    return (
        _RangeScratch.slots.store(SolanaRef.get_blocks(slot_from, slot_to))
        | nu.Log(
            "sync:", slot_from, "->", slot_to, "(", nu.ops.Len(_RangeScratch.slots), "confirmed)"
        )
        | nu.ForEach(
            _RangeScratch.slots,
            sync_slot(ledger, nu.IntAttrRef("slot"), program_id=program_id),
            item="slot",
        )
        | nu.Log("sync complete")
        | nu.Log("synced:", ledger.blocks_meta[AttrRef("slot")].synced)
        | nu.Log("skipped:", ledger.blocks_meta[AttrRef("slot")].skipped)
    )


# =============================================================================
# Main
# =============================================================================


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Solana ledger sync")
    p.add_argument("--slot-from", type=int, required=True, help="Start slot (inclusive)")
    p.add_argument("--slots", type=int, default=100, help="Number of slots to sync")
    p.add_argument(
        "--endpoint", default="https://api.mainnet-beta.solana.com", help="Solana RPC endpoint"
    )
    p.add_argument(
        "--program",
        default="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
        help="Filter: only txs involving this program",
    )
    p.add_argument("--db-path", default=".db-ledger", help="RocksDB storage path")
    return p.parse_args()


async def main() -> None:
    """Run."""
    from virtuals import Navigator

    from nu_virtuals.presets import rocksdb_storage_inmemory

    args = parse_args()

    async with SolanaRpc(endpoint=args.endpoint) as rpc:
        with rocksdb_storage_inmemory(args.db_path) as store:
            nav = Navigator(store)

            ctx = nu.Context().bind(Navigator, nav)
            ctx = ctx.bind(SolanaRpc, rpc)
            ctx = ctx.bind(dict, {})

            slot_to = args.slot_from + args.slots

            app = nu_virtuals.Transaction(
                Ledger.slots_synced.init(set()),
                Ledger.slots_dropped.init(set()),
            ) | sync_range(Ledger, args.slot_from, slot_to, program_id=args.program or "")

            # Deformations: optimize before execution
            app = nu_dict.inline_refs(app)
            app = nu_virtuals.inline_refs(app)
            app = nu_virtuals.auto_atomic(app)
            app = nu_debugger.set_logger_name(app, "sol")

            print(f"syncing slots {args.slot_from} -> {slot_to}")
            print(f"endpoint: {args.endpoint}")
            if args.program:
                print(f"filter: program {args.program}")
            print(f"db: {args.db_path}\n")

            await app.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
