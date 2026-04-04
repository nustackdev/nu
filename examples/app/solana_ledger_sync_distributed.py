#!/usr/bin/env python3
"""Distributed ledger sync -- workers on local Ray, shared RocksDB.

Same shapes and sync logic as solana_ledger_sync.py, different execution:
N Ray workers share a single RocksDB through an invisibles storage service.
Workers interleave slot ranges (stride by N).

Shows: Teleport, Worker, shared storage via invisibles, custom context
resource (per-worker SolanaRpc), worker stride pattern.

    python examples/app/solana_ledger_sync_distributed.py \\
        --slot-from 335000000 --slots 1000 --workers 3
"""

from __future__ import annotations

import argparse
import asyncio
import socket
import tempfile
from typing import Any

import aiohttp
import ray
from composables import Runtime
from composables.spec import SpecBuilder

import nu_dict as ed
import nu_virtuals as ebv
from nu import Context
from nu.abc import IntI, fn, method
from nu.abc.flows import ForRange, If, Log, Parallel, Retry, Seq, TryCatch, While
from nu.core import Ref
from nu.interfaces import ListI
from nu.shape import Shape
from nu_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    InvisiblesServerSpec,
    NavigatorSpec,
    RayActorSpec,
    RayWorkerSpec,
    RocksDBStorageSpec,
    Teleport,
    Worker,
    WorkerSpec,
)


# =============================================================================
# Exceptions (same as single-process version)
# =============================================================================


class RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"RPC error {code}: {message}")


class DroppedSlotError(Exception):
    def __init__(self, slot: int) -> None:
        self.slot = slot
        super().__init__(f"dropped slot {slot}")


# =============================================================================
# RPC client (same as single-process version)
# =============================================================================

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaRpc:
    """Minimal async Solana JSON-RPC client."""

    def __init__(self, endpoint: str = MAINNET, timeout: float = 30.0) -> None:
        self._endpoint = endpoint
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None
        self._id = 0

    async def _ensure_connected(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                connector=aiohttp.TCPConnector(ssl=False),
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

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

    async def get_slot(self) -> int:
        result = await self._call("getSlot", [{"commitment": "confirmed"}])
        return int(result)

    async def get_blocks(self, start: int, end: int) -> list[int]:
        result = await self._call("getBlocks", [start, end, {"commitment": "confirmed"}])
        return [int(s) for s in result]

    async def get_block(self, slot: int) -> list[dict]:
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
        return _parse_block(slot, result)


# =============================================================================
# Block parsing (same as single-process version)
# =============================================================================


def _parse_block(slot: int, data: dict) -> list[dict]:
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


# =============================================================================
# Service declaration (same as single-process version)
# =============================================================================


class SolanaRef(Ref[SolanaRpc]):
    async def resolve(self, ctx: Context) -> str:
        return "solana_rpc"

    async def fetch(self, ctx: Context) -> SolanaRpc:
        return ctx[SolanaRpc]

    get_slot = method(IntI, "get_slot")
    get_blocks = method(ListI, "get_blocks")
    get_block = method(ListI, "get_block")


# =============================================================================
# Shapes (same as single-process version)
# =============================================================================


class Transaction(Shape):
    signature = ebv.StrRef.slot()
    slot_number = ebv.IntRef.slot()
    block_time = ebv.IntRef.slot()
    block_index = ebv.IntRef.slot()
    fee = ebv.IntRef.slot()
    err = ebv.StrRef.slot()
    accounts = ebv.PrimitiveListRef.slot()
    instructions = ebv.PrimitiveListRef.slot()
    inner_instructions = ebv.PrimitiveListRef.slot()
    pre_balances = ebv.PrimitiveListRef.slot()
    post_balances = ebv.PrimitiveListRef.slot()
    pre_token_balances = ebv.PrimitiveListRef.slot()
    post_token_balances = ebv.PrimitiveListRef.slot()
    logs = ebv.PrimitiveListRef.slot()
    compute_units = ebv.IntRef.slot()


TX_ID_MULTIPLIER = 10_000


class Ledger(Shape):
    txs = ebv.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = ebv.PrimitiveSetRef.slot()
    slots_dropped = ebv.PrimitiveSetRef.slot()
    current_slot = ebv.IntRef.slot()


# =============================================================================
# Scratch shapes (per-worker state)
# =============================================================================


class _SlotScratch(Shape):
    """Per-slot scratch for a single slot sync."""

    block_txs = ed.ListRef.slot(object)
    tx_idx = ed.IntRef.slot()
    tx_id = ed.IntRef.slot()


class _WorkerScratch(Shape):
    """Per-worker scratch for stride iteration."""

    cursor = ed.IntRef.slot()


# =============================================================================
# Per-slot sync (same logic as single-process)
# =============================================================================


def _sync_single_slot(ledger: type[Ledger], slot: object, worker_id: int) -> object:
    """Sync one slot with retry and dropped-slot handling."""
    sc = _SlotScratch

    return Retry(
        TryCatch(
            Seq(
                sc.block_txs.store(SolanaRef.get_block(slot)),
                If(
                    fn.Len(sc.block_txs) > 0,
                    ebv.Transaction(
                        ForRange(
                            0,
                            fn.Len(sc.block_txs),
                            Seq(
                                sc.tx_id.store(slot * TX_ID_MULTIPLIER + sc.tx_idx),
                                ledger.txs[sc.tx_id].store(sc.block_txs[sc.tx_idx]),
                            ),
                            index=sc.tx_idx,
                        ),
                        ledger.slots_synced.add(slot),
                    ),
                    ebv.Transaction(ledger.slots_synced.add(slot)),
                ),
                Log("w", worker_id, "slot", slot, ":", fn.Len(sc.block_txs), "txs"),
            ),
            catch=Seq(
                ebv.Transaction(ledger.slots_dropped.add(slot)),
                Log("w", worker_id, "slot", slot, "dropped"),
            ),
            errors=DroppedSlotError,
        ),
        max_attempts=5,
        delay=1,
        backoff=1.5,
        on_attempt_fail=Log("w", worker_id, "retry slot", slot),
        on_fail=Log("w", worker_id, "giving up on slot", slot),
    )


# =============================================================================
# Distributed sync composition
# =============================================================================


def distributed_ledger_sync(
    ledger: type[Ledger],
    slot_from: int,
    slot_to: int,
    num_workers: int,
) -> object:
    """Build distributed sync: N workers stride across slot range.

    Worker 0 syncs slots 0, N, 2N, ...
    Worker 1 syncs slots 1, N+1, 2N+1, ...

    Each worker runs in a separate Ray process via Teleport.
    All workers share a single RocksDB through invisibles.
    """
    worker_teleports = []
    for w in range(num_workers):
        worker_flow = _worker_flow(ledger, slot_from, slot_to, w, num_workers)
        worker_teleports.append(Teleport(worker_flow, worker=w))

    init = ebv.Transaction(
        Seq(
            If(ledger.slots_synced.missing(), ledger.slots_synced.store(set())),
            If(ledger.slots_dropped.missing(), ledger.slots_dropped.store(set())),
        ),
    )

    return Seq(
        init,
        Log(
            "distributed sync:",
            slot_from,
            "->",
            slot_to,
            "workers:",
            num_workers,
        ),
        Parallel(*worker_teleports),
        Log("distributed sync done"),
    )


def _worker_flow(
    ledger: type[Ledger],
    slot_from: int,
    slot_to: int,
    worker_id: int,
    num_workers: int,
) -> object:
    """Single worker: iterate assigned slots in stride order."""
    wc = _WorkerScratch

    return Seq(
        wc.cursor.store(slot_from + worker_id),
        While(
            wc.cursor <= slot_to,
            Seq(
                _sync_single_slot(ledger, wc.cursor, worker_id),
                wc.cursor.store(wc.cursor + num_workers),
            ),
        ),
        Log("w", worker_id, "done"),
    )


# =============================================================================
# Main
# =============================================================================


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Distributed Solana ledger sync")
    p.add_argument("--slot-from", type=int, required=True, help="Start slot (inclusive)")
    p.add_argument("--slots", type=int, default=1000, help="Number of slots to sync")
    p.add_argument("--workers", type=int, default=3, help="Number of Ray workers")
    p.add_argument("--endpoint", default=MAINNET, help="Solana RPC endpoint")
    p.add_argument("--db-path", default=None, help="RocksDB path (default: temp dir)")
    return p.parse_args()


async def main() -> None:
    args = parse_args()
    db_path = args.db_path or tempfile.mkdtemp(prefix="nu-ledger-")

    ray.init()

    try:
        address = f"{ray.util.get_node_ip_address()}:{_free_port()}"
        nav_spec = NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path))

        async with Runtime() as rt:
            # Shared RocksDB served over invisibles (single storage actor)
            await rt.create(
                RayActorSpec(
                    name="storage",
                    inner_spec=InvisiblesServerSpec(
                        transport="tcp",
                        address=address,
                        executor="threaded",
                        root_service=nav_spec,
                    ),
                    actor_name="nu-ledger-storage",
                )
            )

            # Workers: proxied storage, shared RPC endpoint
            proxy_nav = (
                SpecBuilder(nav_spec)
                .as_proxy(InvisiblesClientSpec(transport="tcp", address=address))
                .build()
            )

            ctx = Context()
            for i in range(args.workers):
                w = await rt.create(
                    RayWorkerSpec(
                        name=f"worker-{i}",
                        inner_spec=WorkerSpec(
                            context=ContextSpec(storage=proxy_nav),
                        ),
                        actor_name=f"nu-worker-{i}",
                    )
                )
                ctx = ctx.bind(w, Worker, i)

            # RPC bound at root level. SolanaRpc auto-connects on first use
            # and is picklable (no active session at creation time).
            # For multi-endpoint setups, bind per-worker via custom resource specs.
            rpc = SolanaRpc(endpoint=args.endpoint)
            ctx = ctx.bind(rpc, SolanaRpc)

            slot_to = args.slot_from + args.slots

            # Build and execute
            tree = distributed_ledger_sync(Ledger, args.slot_from, slot_to, args.workers)
            tree = ed.inline_refs(tree)
            tree = ebv.inline_refs(tree)

            print(f"distributed sync: {args.slot_from} -> {slot_to}")
            print(f"workers: {args.workers}, db: {db_path}")
            print(f"endpoint: {args.endpoint}\n")

            await tree.execute(ctx)

    finally:
        ray.shutdown()
        if args.db_path is None:
            import shutil

            shutil.rmtree(db_path, ignore_errors=True)

    print(f"\ndone. {args.workers} ray workers, shared rocksdb, single machine.")


if __name__ == "__main__":
    asyncio.run(main())
