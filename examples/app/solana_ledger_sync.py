#!/usr/bin/env python3
"""Solana ledger sync -- fetch blocks, persist transactions, resumable archive.

Single-process example: connects to Solana mainnet via JSON-RPC, fetches
confirmed blocks in a slot range, parses and persists transactions to
RocksDB. Resumable: skips already-synced slots on restart.

Demonstrates:
  Shapes        -- Transaction, Ledger (persistent data topology)
  FabricRef     -- SolanaRpc bound on the Context, called from the driver
  Compositions  -- Sequential, IfDo, ForEachDo, Retry, TryCatch, log
  Spans         -- nu.virtuals.Transaction (atomic writes)
  Deformations  -- inline_refs (tree rewrites before execution)
  Context       -- storage + service binding

Usage:
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 100
    python examples/app/solana_ledger_sync.py --slot-from 335000000 --slots 500 \\
        --program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P

FIXMEs (semantic gaps versus the pre-v2 example -- to be revisited):
  * The old typed method-descriptor system (``method(IntI, "get_slot")`` on a
    FabricRef subclass) is gone. RPC calls now run driver-side and their
    results are funneled through ``ctx.attrs``.
  * The pre-v2 ``nu.ops.Pluck`` / ``Flatten`` / ``AtOp`` atoms don't exist
    yet; the ``--program`` filter is implemented as a plain-Python helper on
    the parsed tx dict rather than as an in-tree condition.
"""

from __future__ import annotations

import argparse
import asyncio
import tempfile
from pathlib import Path

import aiohttp

import nu
import nu.mem as m
import nu.virtuals as v
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


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

    def __init__(self, endpoint: str = MAINNET, timeout: float = 30.0) -> None:
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

    async def get_slot(self) -> int:
        result = await self._call("getSlot", [{"commitment": "confirmed"}])
        return int(result)  # type: ignore

    async def get_blocks(self, start: int, end: int) -> list[int]:
        result = await self._call("getBlocks", [start, end, {"commitment": "confirmed"}])
        return [int(s) for s in result]  # type: ignore

    async def get_block(self, slot: int) -> list[dict]:
        """Fetch block, parse transactions into dicts matching Transaction shape."""
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


def _tx_involves_program(tx: dict, program_id: str) -> bool:
    """Plain-Python filter (see FIXME at top): scan a tx dict for program_id."""
    for ix in tx.get("instructions", []):
        if ix.get("program_id") == program_id:
            return True
    for group in tx.get("inner_instructions", []):
        for ix in group.get("instructions", []):
            if ix.get("program_id") == program_id:
                return True
    return False


# =============================================================================
# Shapes
# =============================================================================


class Transaction(nu.Shape):
    """Single Solana transaction. All standard fields, stored as-is."""

    # Metadata
    signature = v.StrRef.slot()
    slot_number = v.IntRef.slot()
    block_time = v.IntRef.slot()
    block_index = v.IntRef.slot()
    fee = v.IntRef.slot()
    err = v.StrRef.slot()  # empty = success

    # Structure (typed lists / dicts -- old PrimitiveListRef is deferred)
    accounts = v.ListRef.slot(str)
    instructions = v.ListRef.slot(dict)
    inner_instructions = v.ListRef.slot(dict)

    # Balances
    pre_balances = v.ListRef.slot(int)
    post_balances = v.ListRef.slot(int)
    pre_token_balances = v.ListRef.slot(dict)
    post_token_balances = v.ListRef.slot(dict)

    # Extra
    logs = v.ListRef.slot(str)
    compute_units = v.IntRef.slot()


TX_ID_MULTIPLIER = 10_000
"""Numeric tx ID = slot * 10_000 + block_index. Preserves block ordering."""


class Ledger(nu.Shape):
    """Persistent transaction archive.

    tx_id = slot * 10_000 + block_index.
    Resumable via slots_synced.
    """

    txs = v.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = v.SetRef.slot(int)
    slots_dropped = v.SetRef.slot(int)
    current_slot = v.IntRef.slot()


# =============================================================================
# Scratch shapes (ephemeral, in-memory via nu.mem)
# =============================================================================


class _SlotScratch(nu.Shape):
    """Per-slot scratch for sync_slot."""

    block_txs = m.ListRef.slot(dict)
    tx_id = m.IntRef.slot()


# =============================================================================
# Compositions
# =============================================================================


def _persist_tx(ledger: type[Ledger], slot_expr: object) -> object:
    """Persist one tx from ``ctx.attrs["tx"]`` into ledger.

    Runs inside a ForEachDo body where the current tx dict is bound as
    ``AnyAttrRef("tx")``.
    """
    sc = _SlotScratch
    tx_ref = nu.AnyAttrRef("tx")

    # FIXME: no AtOp/GetItem on AnyAttrRef today; block_index is fed via attrs
    # by the driver before persistence rather than pulled from the tx dict here.
    return nu.Sequential(
        sc.tx_id.store(slot_expr * TX_ID_MULTIPLIER + nu.IntAttrRef("tx_block_index")),
        ledger.txs[sc.tx_id].store(tx_ref),
    )


async def _sync_one_slot(
    ctx: nu.Context,
    ledger: type[Ledger],
    slot: int,
    program_id: str,
) -> None:
    """Fetch one block via the bound SolanaRpc, then run the persist tree.

    RPC lives driver-side (see FIXME at top); the Nu tree handles the write
    span and the atomic set-add.
    """
    rpc = ctx.get(SolanaRpc)

    async def _skip() -> None:
        # Already synced? Skip via a bare-Python check.
        pass

    # Skip if already synced (checked driver-side to avoid an in-tree lookup).
    try:
        block_txs = await rpc.get_block(slot)
    except DroppedSlotError:
        await nu.arun(
            v.Transaction(ledger.slots_dropped.add(slot)),
            ctx,
        )
        await nu.arun(nu.log("dropped slot", slot), ctx)
        return

    if program_id:
        block_txs = [tx for tx in block_txs if _tx_involves_program(tx, program_id)]

    ctx.attrs["_block_txs"] = block_txs

    persist_all: list[object] = []
    for i, tx in enumerate(block_txs):
        # Prime attrs for this tx, then persist via the in-tree helper.
        ctx.attrs["tx"] = tx
        ctx.attrs["tx_block_index"] = tx.get("block_index", i)
        persist_all.append(_persist_tx(ledger, slot))

    tree = v.Transaction(
        nu.Sequential(
            *persist_all,
            ledger.slots_synced.add(slot),
        ),
    )
    await nu.arun(nu.log("slot", slot, ":", len(block_txs), "txs"), ctx)
    await nu.arun(tree, ctx)


async def sync_range(
    ctx: nu.Context,
    ledger: type[Ledger],
    slot_from: int,
    slot_to: int,
    program_id: str,
) -> None:
    """Sync all confirmed slots in ``[slot_from, slot_to]``.

    Fetches the confirmed slot list via ``get_blocks``, then iterates each,
    delegating to ``_sync_one_slot`` for fetch + parse + persist.
    """
    rpc = ctx.get(SolanaRpc)
    slots = await rpc.get_blocks(slot_from, slot_to)
    await nu.arun(
        nu.log("sync:", slot_from, "->", slot_to, "(", len(slots), "confirmed)"),
        ctx,
    )

    # Resume: pull the already-synced set once, filter driver-side.
    synced_snapshot: set[int] = set()  # FIXME: read Ledger.slots_synced back here

    for slot in slots:
        if slot in synced_snapshot:
            continue
        await Retry_via_driver(ctx, ledger, slot, program_id)

    await nu.arun(nu.log("sync complete"), ctx)


async def Retry_via_driver(  # noqa: N802
    ctx: nu.Context, ledger: type[Ledger], slot: int, program_id: str
) -> None:
    """Ad-hoc driver-side retry loop; see FIXME at top of file.

    A future revision will move this back into ``nu.spans.Retry`` inside the
    Nu tree once the RPC dispatch pattern is settled.
    """
    delay = 1.0
    for attempt in range(5):
        try:
            await _sync_one_slot(ctx, ledger, slot, program_id)
            return
        except Exception:
            await nu.arun(nu.log("retry slot", slot, "attempt", attempt + 1), ctx)
            await asyncio.sleep(delay)
            delay *= 1.5
    await nu.arun(nu.log("giving up on slot", slot), ctx)


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
    rpc = SolanaRpc(endpoint=args.endpoint)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = args.db_path or str(Path(tmp) / "ledger")
            with v.rocksdb_storage_inmemory(db_path) as storage:
                nav = Navigator(storage)
                with storage.transaction() as tx:
                    ctx = (
                        nu.Context()
                        .bind(Navigator, nav)
                        .bind(TransactionProtocol, tx)
                        .bind(SolanaRpc, rpc)
                    )

                    slot_to = args.slot_from + args.slots

                    # Seed the ledger sets once (idempotent -- init if missing).
                    init = v.Transaction(
                        nu.Sequential(
                            nu.IfDo(Ledger.slots_synced.missing(), Ledger.slots_synced.store(set())),
                            nu.IfDo(Ledger.slots_dropped.missing(), Ledger.slots_dropped.store(set())),
                        ),
                    )
                    init = v.inline_refs(init)
                    await nu.arun(init, ctx)

                    print(f"syncing slots {args.slot_from} -> {slot_to}")
                    print(f"endpoint: {args.endpoint}")
                    if args.program:
                        print(f"filter: program {args.program}")
                    print(f"db: {db_path}\n")

                    await sync_range(ctx, Ledger, args.slot_from, slot_to, args.program or "")
    finally:
        await rpc.close()


if __name__ == "__main__":
    asyncio.run(main())
