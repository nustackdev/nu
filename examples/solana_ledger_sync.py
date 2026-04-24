#!/usr/bin/env python3
"""Solana ledger sync -- fetch blocks, persist transactions, resumable archive.

Usage:
    python examples/solana_ledger_sync.py --slot-from 335000000 --slots 100
    python examples/solana_ledger_sync.py --slot-from 335000000 --slots 500 \\
        --program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
"""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

import aiohttp

import nu
import nu_dict
import nu_virtuals
import nu_virtuals as nv
from nu.stdlib import TimeSleep


class DroppedSlotError(Exception):
    pass


# -- RPC client ---------------------------------------------------------------


class SolanaRpc:
    """Minimal async Solana JSON-RPC client."""

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._session: aiohttp.ClientSession | None = None
        self._id = 0

    async def _call(self, method: str, params: list | None = None) -> Any:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        self._id += 1
        async with self._session.post(
            self._endpoint,
            json={"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or []},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if "error" in data:
            code = data["error"].get("code") if isinstance(data["error"], dict) else None
            if code in (-32009, -32007):
                raise DroppedSlotError(data["error"])
            raise RuntimeError(data["error"])
        return data.get("result")

    async def get_block(self, slot: int) -> dict:
        """Fetch block, return {"slot": slot, "txs": [tx dicts]}."""
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
        if result is None:
            raise DroppedSlotError(slot)
        block_time = result.get("blockTime", 0) or 0
        txs = []
        for i, raw in enumerate(result.get("transactions", [])):
            tx, meta = raw.get("transaction", {}), raw.get("meta", {})
            if not tx:
                continue
            msg = tx.get("message", {})
            accounts = list(msg.get("accountKeys", []))
            for t in ("writable", "readonly"):
                accounts.extend(meta.get("loadedAddresses", {}).get(t, []))
            all_ixs = list(msg.get("instructions", []))
            for inner in meta.get("innerInstructions", []):
                all_ixs.extend(inner.get("instructions", []))
            programs = {
                accounts[ix.get("programIdIndex", 0)]
                for ix in all_ixs
                if ix.get("programIdIndex", 0) < len(accounts)
            }
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
        return {"slot": slot, "txs": txs}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        await self.close()


# -- Service declaration ------------------------------------------------------


class SolanaRef(nu.Ref[SolanaRpc]):
    """Ref that resolves SolanaRpc from Context. Invocation descriptors create lazy terms.

    Resolution is sync (ctx.get). Per-method async lives on the Invoke nodes
    that Invocation descriptors produce; each carries its own mode.
    """

    own_mode: ClassVar[nu.Mode] = nu.Mode.BOTH
    func_mode: ClassVar[nu.Mode] = nu.Mode.SYNC

    def resolve(self, ctx: nu.Context) -> str:
        return "solana_rpc"

    def fetch(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    async def aresolve(self, ctx: nu.Context) -> str:
        return self.resolve(ctx)

    async def afetch(self, ctx: nu.Context) -> SolanaRpc:
        return self.fetch(ctx)

    get_block = nu.Invocation(nu.DictI, "get_block", mode=(nu.Mode.ASYNC, nu.Mode.ASYNC))


# -- Shapes -------------------------------------------------------------------


class Transaction(nu.Shape):
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
    inner_instructions = nu_virtuals.PrimitiveListRef.slot()  # primitive blobs
    log_messages = nu_virtuals.PrimitiveListRef.slot()


class BlockMeta(nu.Shape):
    synced = nu_virtuals.IntRef.slot()
    skipped = nu_virtuals.IntRef.slot()


class Ledger(nu.Shape):
    """Persistent transaction archive. Resumable via slots_synced."""

    txs = nu_virtuals.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = nu_virtuals.PrimitiveSetRef.slot()
    slots_dropped = nu_virtuals.PrimitiveSetRef.slot()
    current_slot = nu_virtuals.IntRef.slot()
    blocks_meta = nu_virtuals.ShapesDictRef.slot(BlockMeta, key_type=int)


class _SlotScratch(nu.Shape):
    tx_id = nu_dict.IntRef.slot()


class _RangeScratch(nu.Shape):
    blocks = nu_dict.ListRef.slot(dict)  # {"slot": int, "txs": list[dict]}
    cursor = nu_dict.IntRef.slot()


# -- Compositions -------------------------------------------------------------


def _persist_tx(ledger: type[Ledger], slot: nu.IntArg) -> nu.Nu:
    # tx_id = slot * 10_000 + block_index
    return _SlotScratch.tx_id.store(
        nu.IntI(slot) * 10_000 + nu.At(nu.AttrRef("tx"), "block_index")
    ) >> ledger.txs[_SlotScratch.tx_id].store(nu.DictAttrRef("tx"))


def fetcher(
    ledger: type[Ledger], slot_from: int, slot_count: int, worker_id: int, n_workers: int
) -> nu.Nu:
    """One fetch branch. Strides ``[slot_from + worker_id, slot_from + slot_count)``
    by ``n_workers``, pulls each block, appends an entry to ``_RangeScratch.blocks``.
    On drop: logs and skips (no append).
    """
    slot = nu.IntAttrRef(f"slot_{worker_id}")
    return nu.ForRange(
        slot_from + worker_id,
        slot_from + slot_count,
        nu.Retry(
            nu.TryCatch(
                _RangeScratch.blocks.append(SolanaRef.get_block(slot))
                >> nu.Log("slot arrived:", slot),
                nu.Log("dropped slot (skipping):", slot) >> ledger.slots_dropped.add(slot),
                errors=DroppedSlotError,
            ),
            max_attempts=5,
            delay=1,
            backoff=1.5,
            on_attempt_fail=nu.Log("retry slot", slot),
            on_fail=nu.Log("giving up on slot", slot),
        ),
        step=n_workers,
        index=f"slot_{worker_id}",
    )


def process_entry(ledger: type[Ledger], entry_ref: nu.Nu, *, program_id: nu.StrArg = "") -> nu.Nu:
    """Persist one fetched block entry."""
    slot = nu.IntI(nu.At(entry_ref, "slot"))
    bm = ledger.blocks_meta[slot]
    return (
        bm.skipped.init(0)
        >> bm.synced.init(0)
        >> nv.Transaction(
            nu.ForEach(
                nu.At(entry_ref, "txs"),
                nu.IfDo(
                    nu.ToBool(program_id),
                    nu.If(
                        nu.Contains(nu.DictAttrRef("tx").get("programs"), program_id),
                        bm.synced.inc() >> _persist_tx(ledger, slot),
                        bm.skipped.inc(),
                    ),
                    bm.synced.inc() >> _persist_tx(ledger, slot),
                ),
                item="tx",
            )
        )
        >> ledger.slots_synced.add(slot)
    )


def processor(ledger: type[Ledger], *, program_id: nu.StrArg = "") -> nu.Nu:
    """Sync consumer. Polls ``_RangeScratch.blocks`` at ``cursor``, persists,
    increments cursor. Polls indefinitely with a 50ms sleep when caught up.
    Runs on a worker thread under ``max_parallel >= 2``.
    """
    entry = _RangeScratch.blocks[_RangeScratch.cursor]
    return nu.Forever(
        nu.If(
            nu.Lt(_RangeScratch.cursor, nu.Len(_RangeScratch.blocks)),
            process_entry(ledger, entry, program_id=program_id) >> _RangeScratch.cursor.inc(),
            TimeSleep(0.05),
        ),
    )


def sync_range(
    ledger: type[Ledger],
    slot_from: int,
    slot_count: int,
    *,
    program_id: nu.StrArg = "",
    n_workers: int = 5,
) -> nu.Nu:
    """Sync ``slot_count`` slots starting at ``slot_from``.

    ``n_workers`` async fetchers pull blocks concurrently (striped modulo
    n_workers) into ``_RangeScratch.blocks``; one sync processor drains the
    list and persists each entry. Fetchers share the event loop; the processor
    runs on a worker thread. Needs ``max_parallel >= 2`` at execution time.
    """
    return (
        Ledger.slots_synced.init(set())
        >> Ledger.slots_dropped.init(set())
        >> _RangeScratch.blocks.store([])
        >> _RangeScratch.cursor.init(0)
        >> nu.Log("sync:", slot_from, "->", slot_from + slot_count)
        >> (
            fetcher(ledger, slot_from, slot_count, 0, n_workers)
            | fetcher(ledger, slot_from, slot_count, 1, n_workers)
            | fetcher(ledger, slot_from, slot_count, 2, n_workers)
            | fetcher(ledger, slot_from, slot_count, 3, n_workers)
            | processor(ledger, program_id=program_id)
        )
    )


def reactive_stats(ledger: type[Ledger]) -> nu.Nu:
    """Reactive observers: log block arrivals and per-block synced/skipped counters."""
    return (
        nu.shapes.ReactForever(
            ledger.blocks_meta.on_descendants_change("*"),
            nu.Log("new block:", nu.At(nu.TupleAttrRef("slot_change"), -1)),
            changed_key="slot_change",
        )
        | nu.shapes.ReactForever(
            ledger.blocks_meta.on_descendants_change("*", "skipped"),
            nu.Throttle(
                0.2,
                nu.Log(
                    "block",
                    nu.At(nu.TupleAttrRef("skipped_change"), -2),
                    "txs skipped:",
                    ledger.blocks_meta[nu.At(nu.TupleAttrRef("skipped_change"), -2)].skipped,
                ),
            ),
            changed_key="skipped_change",
        )
        | nu.shapes.ReactForever(
            ledger.blocks_meta.on_descendants_change("*", "synced"),
            nu.Throttle(
                0.2,
                nu.Log(
                    "block",
                    nu.At(nu.TupleAttrRef("synced_change"), -2),
                    "txs synced:",
                    ledger.blocks_meta[nu.At(nu.TupleAttrRef("synced_change"), -2)].synced,
                ),
            ),
            changed_key="synced_change",
        )
    )


# -- Main ---------------------------------------------------------------------


async def main() -> None:
    import argparse
    import logging

    import nu_inspect
    from nu_virtuals.presets import rocksdb_storage_inmemory
    from virtuals import Navigator

    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("sol")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.propagate = False

    # Parse CLI args
    p = argparse.ArgumentParser(description="Solana ledger sync")
    p.add_argument("--slot-from", type=int, default=408000000)
    p.add_argument("--slots", type=int, default=20)
    p.add_argument("--endpoint", default="https://api.mainnet-beta.solana.com")
    p.add_argument("--program", default="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
    p.add_argument("--db-path", default=".db-ledger")
    p.add_argument(
        "--workers", type=int, default=5, help="concurrent fetchers; processor is 1 extra thread"
    )
    p.add_argument(
        "--max-parallel",
        type=int,
        default=2,
        help="tree-wide threading budget (>=2 for concurrent fetch/process)",
    )
    args = p.parse_args()

    # Init services
    async with SolanaRpc(endpoint=args.endpoint) as rpc:
        with rocksdb_storage_inmemory(args.db_path) as store:
            # Prepare the execution context
            ctx = nu.Context()
            ctx = ctx.bind(Navigator, Navigator(store))
            ctx = ctx.bind(SolanaRpc, rpc)
            ctx = ctx.bind(dict, {})

            # Construct the app
            app = (
                (
                    nu.Log("--- sync ---")
                    >> nu.Log("syncing", args.slots, "slots from", args.slot_from)
                    >> nu.Log("endpoint:", args.endpoint)
                    >> nu.Log("filter: program", args.program or "(none)")
                    >> nu.Log("db:", args.db_path)
                )
                >> (
                    sync_range(
                        Ledger,
                        args.slot_from,
                        args.slots,
                        program_id=args.program or "",
                        n_workers=args.workers,
                    )
                    | reactive_stats(Ledger)
                )
                >> (
                    nu.Log("--- sync report ---")
                    >> nu.Log(
                        "txs synced",
                        nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "synced")),
                    )
                    >> nu.Log(
                        "txs skipped",
                        nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "skipped")),
                    )
                )
            )

            # Apply app meta-transformations
            app = nu_dict.inline_refs(app)
            app = nu_virtuals.inline_refs(app)
            app = nu_virtuals.auto_atomic(app)
            app = nu_inspect.set_logger_name(app, "sol")

            # Print the app
            # print(nu_inspect.render_nu(app))

            # Execute the app
            await asyncio.gather(
                app.aexecute(ctx, max_parallel=args.max_parallel),
                # nudle.arun_ui(Ledger, ctx),
            )


if __name__ == "__main__":
    asyncio.run(main())
