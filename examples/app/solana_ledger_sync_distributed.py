#!/usr/bin/env python3
"""Distributed ledger sync -- workers on local Ray, shared RocksDB.

Same shapes as solana_ledger_sync.py, different execution: N Ray workers
share a single RocksDB through an invisibles storage service. Workers
interleave slot ranges (stride by N).

Shows: Teleport, Worker, shared storage via invisibles, custom context
resource (per-worker SolanaRpc), worker stride pattern.

    python examples/app/solana_ledger_sync_distributed.py \\
        --slot-from 335000000 --slots 1000 --workers 3

FIXMEs (same drift as the single-process example):
  * The old typed method-descriptor system (``method(IntI, "get_slot")`` on a
    ServiceRef subclass) is gone; RPC calls run driver-side per worker and
    their results are funneled through ``ctx.attrs``.
  * The pre-v2 ``nu.ops.Pluck`` / ``Flatten`` atoms don't exist; the
    ``--program`` filter is a plain-Python helper.
"""

from __future__ import annotations

import argparse
import asyncio
import socket
import tempfile
from typing import Any

import aiohttp
import ray

import nu
import nu.mem as m
import nu.virtuals as v
from composables import Runtime
from composables.spec import SpecBuilder
from nu.distributed import (
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
# Shapes (same as single-process version)
# =============================================================================


class Transaction(nu.Shape):
    signature = v.StrRef.slot()
    slot_number = v.IntRef.slot()
    block_time = v.IntRef.slot()
    block_index = v.IntRef.slot()
    fee = v.IntRef.slot()
    err = v.StrRef.slot()
    accounts = v.ListRef.slot(str)
    instructions = v.ListRef.slot(dict)
    inner_instructions = v.ListRef.slot(dict)
    pre_balances = v.ListRef.slot(int)
    post_balances = v.ListRef.slot(int)
    pre_token_balances = v.ListRef.slot(dict)
    post_token_balances = v.ListRef.slot(dict)
    logs = v.ListRef.slot(str)
    compute_units = v.IntRef.slot()


TX_ID_MULTIPLIER = 10_000


class Ledger(nu.Shape):
    txs = v.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = v.SetRef.slot(int)
    slots_dropped = v.SetRef.slot(int)
    current_slot = v.IntRef.slot()


# =============================================================================
# Scratch shapes (per-worker state)
# =============================================================================


class _SlotScratch(nu.Shape):
    """Per-slot scratch for a single slot sync."""

    block_txs = m.ListRef.slot(dict)
    tx_id = m.IntRef.slot()


class _WorkerScratch(nu.Shape):
    """Per-worker scratch for stride iteration."""

    cursor = m.IntRef.slot()


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

    FIXME: the per-worker body used to be a full Nu tree (Retry/TryCatch,
    ServiceRef.get_block, ForRangeDo, etc.). Given the current gaps around
    typed RPC dispatch and inline_refs on the mem fabric, the worker body is
    left as a shell here -- the driver-side loop from the single-process
    version applies inside each worker until we settle the pattern.
    """
    worker_teleports = []
    for w in range(num_workers):
        worker_teleports.append(Teleport(nu.Sequential(), worker=w))  # FIXME: shell body

    init = v.Transaction(
        nu.Sequential(
            nu.IfDo(ledger.slots_synced.missing(), ledger.slots_synced.store(set())),
            nu.IfDo(ledger.slots_dropped.missing(), ledger.slots_dropped.store(set())),
        ),
    )

    return nu.Sequential(
        init,
        nu.log(
            "distributed sync:",
            slot_from,
            "->",
            slot_to,
            "workers:",
            num_workers,
        ),
        nu.Parallel(*worker_teleports),
        nu.log("distributed sync done"),
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

            ctx = nu.Context()
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
                ctx = ctx.bind(Worker, w, i)

            # RPC bound at root level. SolanaRpc auto-connects on first use
            # and is picklable (no active session at creation time).
            # For multi-endpoint setups, bind per-worker via custom resource specs.
            rpc = SolanaRpc(endpoint=args.endpoint)
            ctx = ctx.bind(SolanaRpc, rpc)

            slot_to = args.slot_from + args.slots

            # Build and execute
            tree = distributed_ledger_sync(Ledger, args.slot_from, slot_to, args.workers)

            print(f"distributed sync: {args.slot_from} -> {slot_to}")
            print(f"workers: {args.workers}, db: {db_path}")
            print(f"endpoint: {args.endpoint}\n")

            await nu.arun(tree, ctx)

    finally:
        ray.shutdown()
        if args.db_path is None:
            import shutil

            shutil.rmtree(db_path, ignore_errors=True)

    print(f"\ndone. {args.workers} ray workers, shared rocksdb, single machine.")


if __name__ == "__main__":
    asyncio.run(main())
