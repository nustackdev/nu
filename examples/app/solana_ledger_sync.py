#!/usr/bin/env python3
"""Solana ledger sync -- fetch blocks, persist transactions, resumable archive.

Single-process example: connects to Solana mainnet via JSON-RPC, fetches
confirmed blocks in a slot range, parses and persists transactions to
RocksDB. Resumable: skips already-synced slots on restart.

Demonstrates:
  Shapes        -- Transaction, Ledger (persistent data topology)
  Ref + method  -- typed, lazy RPC access via method descriptors
  Compositions  -- Seq, If, ForEach, Filter, Retry, TryCatch, Log
  Spans         -- nu_virtuals.Transaction (atomic writes)
  Deformations  -- inline_refs (tree rewrites before execution)
  Context       -- storage + service binding

Usage:
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 100
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 500 \\
        --program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
"""

from __future__ import annotations

import argparse

import aiohttp

import nu
import nu_dict
import nu_virtuals


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
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout
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

    async def _call(self, method: str, params: list | None = None) -> object:
        await self._ensure_connected()
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or []}
        if self._session is None:
            raise ValueError("Session not attached")
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
        return int(result)  # type: ignore

    async def get_blocks(self, start: int, end: int) -> list[int]:
        result = await self._call("getBlocks", [start, end, {"commitment": "confirmed"}])
        return [int(s) for s in result]  # type: ignore

    async def get_block(self, slot: int) -> list[dict]:
        """Fetch block, parse transactions into dicts matching Transaction shape.

        Returns all transactions. Program filtering is done in the composition.
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

        return _parse_block(slot, result)  # type: ignore


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
    """Single Solana transaction. All standard fields, stored as-is.

    Scalar fields are individually addressable. Lists (accounts, instructions,
    balances, logs) are primitive blobs -- stored and read whole.
    """

    # Metadata
    signature = nu_virtuals.StrRef.slot()
    slot_number = nu_virtuals.IntRef.slot()
    block_time = nu_virtuals.IntRef.slot()
    block_index = nu_virtuals.IntRef.slot()
    fee = nu_virtuals.IntRef.slot()
    err = nu_virtuals.StrRef.slot()  # empty = success

    # Structure (primitive blobs)
    accounts = nu_virtuals.PrimitiveListRef.slot()
    instructions = nu_virtuals.PrimitiveListRef.slot()
    inner_instructions = nu_virtuals.PrimitiveListRef.slot()

    # Balances (primitive blobs)
    pre_balances = nu_virtuals.PrimitiveListRef.slot()
    post_balances = nu_virtuals.PrimitiveListRef.slot()
    pre_token_balances = nu_virtuals.PrimitiveListRef.slot()
    post_token_balances = nu_virtuals.PrimitiveListRef.slot()

    # Extra
    logs = nu_virtuals.PrimitiveListRef.slot()
    compute_units = nu_virtuals.IntRef.slot()


TX_ID_MULTIPLIER = 10_000
"""Numeric tx ID = slot * 10_000 + block_index. Preserves block ordering."""


class Ledger(nu.shapes.Shape):
    """Persistent transaction archive.

    tx_id = slot * 10_000 + block_index.
    Resumable via slots_synced.
    """

    txs = nu_virtuals.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = nu_virtuals.PrimitiveSetRef.slot()
    slots_dropped = nu_virtuals.PrimitiveSetRef.slot()
    current_slot = nu_virtuals.IntRef.slot()


# =============================================================================
# Scratch shapes (ephemeral, in-memory via nu_dict)
# =============================================================================


class _SlotScratch(nu.shapes.Shape):
    """Per-slot scratch for sync_slot."""

    block_txs = nu_dict.ListRef.slot(object)
    tx_id = nu_dict.IntRef.slot()


class _RangeScratch(nu.shapes.Shape):
    """Scratch for sync_range iteration."""

    slots = nu_dict.ListRef.slot(int)


# =============================================================================
# Compositions
# =============================================================================


def _involves_program(program_id: nu.StrArg) -> nu.Nu:
    """Nu condition: does ctx.attrs["tx"] involve the given program?

    All tree nodes, all lazy, short-circuits on first match.
    Equivalent to nested for loops checking program_id across
    top-level and inner instructions.
    """
    ixs = nu.AnyI(nu.AtOp(nu.AnyAttrRef("tx"), "instructions"))
    inner = nu.AnyI(nu.AtOp(nu.AnyAttrRef("tx"), "inner_instructions"))

    # top-level: program_id in [ix["program_id"] for ix in instructions]
    top_match = nu.ops.Contains(nu.ops.Pluck(ixs, "program_id"), program_id)

    # inner: flatten inner_instructions[*].instructions, same check
    inner_programs = nu.ops.Pluck(nu.ops.Flatten(nu.ops.Pluck(inner, "instructions")), "program_id")
    inner_match = nu.ops.Contains(inner_programs, program_id)

    return top_match.or_(inner_match)


def _persist_tx(ledger: type[Ledger], slot: nu.IntArg) -> nu.Nu:
    """Persist one tx from ctx.attrs["tx"] to ledger."""
    sc = _SlotScratch

    return nu.Seq(
        sc.tx_id.store(nu.IntI(slot) * TX_ID_MULTIPLIER + nu.AtOp(nu.AttrRef("tx"), "block_index")),
        ledger.txs[sc.tx_id].store(nu.AnyAttrRef("tx")),
    )


def sync_slot(ledger: type[Ledger], slot: nu.IntArg, *, program_id: nu.StrArg = "") -> nu.Nu:
    """Fetch one block, parse txs, persist atomically. Skip if already synced.

    When program_id is truthy, only persists txs involving that program.
    The filter decision is in the tree -- fully dynamic via If(ToBool(...)).
    """
    sc = _SlotScratch
    persist = _persist_tx(ledger, slot)

    iterate_txs = nu.If(
        nu.ops.ToBool(program_id),
        nu.Filter(sc.block_txs, condition=_involves_program(program_id), body=persist, item="tx"),
        nu.ForEach(sc.block_txs, persist, item="tx"),
    )

    return nu.If(
        nu.ops.Contains(ledger.slots_synced, slot).not_(),
        nu.Retry(
            nu.TryCatch(
                nu.Seq(
                    sc.block_txs.store(SolanaRef.get_block(slot)),
                    nu.Log("slot", slot, ":", nu.ops.Len(sc.block_txs), "txs"),
                    nu_virtuals.Transaction(
                        iterate_txs,
                        ledger.slots_synced.add(slot),
                    ),
                ),
                catch=nu.Seq(
                    nu_virtuals.Transaction(ledger.slots_dropped.add(slot)),
                    nu.Log("dropped slot", slot),
                ),
                errors=DroppedSlotError,
            ),
            max_attempts=5,
            delay=1,
            backoff=1.5,
            on_attempt_fail=nu.Log("retry slot", slot),
            on_fail=nu.Log("giving up on slot", slot),
        ),
    )


def sync_range(
    ledger: type[Ledger], slot_from: int, slot_to: int, *, program_id: nu.StrArg = ""
) -> nu.Nu:
    """Sync all confirmed slots in [slot_from, slot_to].

    Fetches the confirmed slot list via get_blocks(), then iterates each,
    delegating to sync_slot for fetch + parse + persist.
    """
    sc = _RangeScratch
    slot = nu.IntAttrRef("slot")

    return nu.Seq(
        sc.slots.store(SolanaRef.get_blocks(slot_from, slot_to)),
        nu.Log("sync:", slot_from, "->", slot_to, "(", nu.ops.Len(sc.slots), "confirmed)"),
        nu.ForEach(
            sc.slots,
            sync_slot(ledger, slot, program_id=program_id),
            item="slot",
        ),
        nu.Log("sync complete"),
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

    from virtuals.tkv.storage import StorageProtocol

    from nu_virtuals.presets import rocksdb_storage_inmemory

    args = parse_args()

    rpc = SolanaRpc(endpoint=args.endpoint)

    try:
        with rocksdb_storage_inmemory(args.db_path) as store:
            ctx = nu.Context().bind(StorageProtocol, store).bind(SolanaRpc, rpc)

            slot_to = args.slot_from + args.slots

            # Build composition: init ledger state, then sync range
            init = nu_virtuals.Transaction(
                nu.Seq(
                    nu.If(Ledger.slots_synced.missing(), Ledger.slots_synced.store(set())),
                    nu.If(Ledger.slots_dropped.missing(), Ledger.slots_dropped.store(set())),
                ),
            )
            tree = nu.Seq(
                init,
                sync_range(Ledger, args.slot_from, slot_to, program_id=args.program or ""),
            )

            # Deformations: optimize before execution
            tree = nu_dict.inline_refs(tree)
            tree = nu_virtuals.inline_refs(tree)

            print(f"syncing slots {args.slot_from} -> {slot_to}")
            print(f"endpoint: {args.endpoint}")
            if args.program:
                print(f"filter: program {args.program}")
            print(f"db: {args.db_path}\n")

            await tree.execute(ctx)
    finally:
        await rpc.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
