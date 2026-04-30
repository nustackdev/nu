#!/usr/bin/env python3
"""Solana block archive -- fetch blocks, persist transactions as-is.

Same orchestration as `solana_ledger_sync.py` (parallel fetchers + sync
processor + reactive stats + snapshot report) -- but the Tx shape and the
RPC client mirror the JSON-RPC `getBlock` response verbatim. No field
flattening, no per-tx massaging in the RPC client.

Usage:
    python examples/solana_block_archive.py --slot-from 408000000 --slots 20
"""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

import aiohttp

import nu
import nu_mem as nm
import nu_virtuals
import nu_virtuals as nv
import nudle
from nu import runtime
from nu.stdlib import TimeSleep


class DroppedSlotError(Exception):
    pass


# -- RPC client ---------------------------------------------------------------


class SolanaRpc:
    """Minimal async Solana JSON-RPC client. Returns raw `result` payload."""

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
        """Fetch block; return ``{"slot": slot, "block": <raw result>}``."""
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
        return {"slot": slot, "block": result}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        await self.close()


# -- Service declaration ------------------------------------------------------


class SolanaRef(nu.Ref[SolanaRpc]):
    support: ClassVar[frozenset[nu.Mode]] = frozenset({nu.Mode.SYNC, nu.Mode.ASYNC})

    def eval(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    async def aeval(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    get_block = nu.Invocation(nu.DictForm, "get_block", support=frozenset({nu.Mode.ASYNC}))


# -- Shapes (mirror RPC structure verbatim) -----------------------------------


class TxMessage(nu.Shape):
    accountKeys = nv.PrimitiveListRef.slot()
    recentBlockhash = nv.StrRef.slot()
    instructions = nv.PrimitiveListRef.slot()
    header = nv.PrimitiveDictRef.slot()
    addressTableLookups = nv.PrimitiveListRef.slot()


class TxInner(nu.Shape):
    signatures = nv.PrimitiveListRef.slot()
    message = nv.ShapeRef.slot(TxMessage)


class TxMeta(nu.Shape):
    err = nv.PrimitiveDictRef.slot()
    fee = nv.IntRef.slot()
    preBalances = nv.PrimitiveListRef.slot()
    postBalances = nv.PrimitiveListRef.slot()
    innerInstructions = nv.PrimitiveListRef.slot()
    logMessages = nv.PrimitiveListRef.slot()
    preTokenBalances = nv.PrimitiveListRef.slot()
    postTokenBalances = nv.PrimitiveListRef.slot()
    loadedAddresses = nv.PrimitiveDictRef.slot()
    computeUnitsConsumed = nv.IntRef.slot()
    status = nv.PrimitiveDictRef.slot()


class Transaction(nu.Shape):
    transaction = nv.ShapeRef.slot(TxInner)
    meta = nv.ShapeRef.slot(TxMeta)
    version = nv.StrRef.slot()


class BlockMeta(nu.Shape):
    synced = nv.IntRef.slot()
    skipped = nv.IntRef.slot()


class Ledger(nu.Shape):
    """Persistent transaction archive. Resumable via slots_synced."""

    txs = nv.ShapesDictRef.slot(Transaction, key_type=int)
    slots_synced = nv.PrimitiveSetRef.slot()
    slots_dropped = nv.PrimitiveSetRef.slot()
    current_slot = nv.IntRef.slot()
    blocks_meta = nv.ShapesDictRef.slot(BlockMeta, key_type=int)
    fetch_done = nv.BoolRef.slot()


class _SlotScratch(nu.Shape):
    tx_idx = nm.IntRef.slot()
    tx_id = nm.IntRef.slot()


class _RangeScratch(nu.Shape):
    blocks = nm.ListRef.slot(dict)  # {"slot": int, "block": <raw RPC dict>}
    cursor = nm.IntRef.slot()


# -- Compositions -------------------------------------------------------------


def _persist_tx(ledger: type[Ledger], slot: nu.IntArg) -> nu.Nu:
    """tx_id = slot * 10_000 + per-block tx index. Store the raw tx dict."""
    return (
        _SlotScratch.tx_id.store(nu.IntForm(slot) * 10_000 + _SlotScratch.tx_idx)
        >> ledger.txs[_SlotScratch.tx_id].store(nu.DictAttrRef("tx"))
        >> _SlotScratch.tx_idx.inc()
    )


def fetcher(
    ledger: type[Ledger], slot_from: int, slot_count: int, worker_id: int, n_workers: int
) -> nu.Nu:
    """One fetch branch. Strides by ``n_workers``, pulls each block, appends the
    raw entry to ``_RangeScratch.blocks``. On drop: log + skip.
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
    """Persist one fetched block entry. ``entry_ref`` is ``{"slot", "block"}``."""
    slot = nu.IntForm(nu.At(entry_ref, "slot"))
    block = nu.At(entry_ref, "block")
    bm = ledger.blocks_meta[slot]
    # Filter: program_id appears in tx.transaction.message.accountKeys.
    tx_account_keys = nu.At(nu.At(nu.At(nu.AttrRef("tx"), "transaction"), "message"), "accountKeys")
    return (
        bm.skipped.init(0)
        >> bm.synced.init(0)
        >> _SlotScratch.tx_idx.store(0)
        >> nv.Transaction(
            nu.ForEach(
                nu.At(block, "transactions"),
                nu.IfDo(
                    nu.ToBool(program_id),
                    nu.IfDo(
                        nu.Contains(tx_account_keys, program_id),
                        bm.synced.inc() >> _persist_tx(ledger, slot),
                        # bm.skipped.inc(),
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
    increments cursor. Sleeps 50ms when caught up. Terminates when fetchers
    finish (``fetch_done``) and the buffer is fully drained. Runs on a worker
    thread under ``max_parallel >= 2``.
    """
    entry = _RangeScratch.blocks[_RangeScratch.cursor]
    return nu.DoWhile(
        nu.or_(ledger.fetch_done.not_(), _RangeScratch.cursor < nu.Len(_RangeScratch.blocks)),
        nu.IfDo(
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
    n_workers: int = 6,
) -> nu.Nu:
    """Sync ``slot_count`` slots starting at ``slot_from``.

    ``n_workers`` async fetchers stream blocks into ``_RangeScratch.blocks``;
    one sync processor drains the list and persists each entry. Fetchers share
    the event loop; the processor runs on a worker thread. Needs
    ``max_parallel >= 2``.
    """
    return (
        Ledger.slots_synced.init(set())
        >> Ledger.slots_dropped.init(set())
        >> _RangeScratch.blocks.store([])
        >> _RangeScratch.cursor.init(0)
        >> nu.Log("sync:", slot_from, "->", slot_from + slot_count)
        >> (
            (
                (
                    fetcher(ledger, slot_from, slot_count, 0, n_workers)
                    | fetcher(ledger, slot_from, slot_count, 1, n_workers)
                    | fetcher(ledger, slot_from, slot_count, 2, n_workers)
                    | fetcher(ledger, slot_from, slot_count, 3, n_workers)
                    | fetcher(ledger, slot_from, slot_count, 4, n_workers)
                    | fetcher(ledger, slot_from, slot_count, 5, n_workers)
                )
                >> Ledger.fetch_done.store(True)
            )
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

    p = argparse.ArgumentParser(description="Solana block archive")
    p.add_argument("--slot-from", type=int, default=408000000)
    p.add_argument("--slots", type=int, default=20)
    p.add_argument(
        "--endpoint",
        default="https://mainnet.helius-rpc.com/?api-key=ebf174cb-9472-4232-93f3-81bd3044b0c4",
    )
    p.add_argument("--program", default="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
    p.add_argument("--db-path", default=".db-archive")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--max-parallel", type=int, default=10)
    args = p.parse_args()

    async with SolanaRpc(endpoint=args.endpoint) as rpc:
        with rocksdb_storage_inmemory(args.db_path) as store:
            ctx = nu.Context()
            ctx = ctx.bind(Navigator, Navigator(store))
            ctx = ctx.bind(SolanaRpc, rpc)
            ctx = ctx.bind(dict, {})

            app = (
                (
                    nu.Log("--- sync ---")
                    >> nu.Log("syncing", args.slots, "slots from", args.slot_from)
                    >> nu.Log("endpoint:", args.endpoint)
                    >> nu.Log("filter: program", args.program or "(none)")
                    >> nu.Log("db:", args.db_path)
                    >> Ledger.fetch_done.store(False)
                )
                >> (
                    sync_range(
                        Ledger,
                        args.slot_from,
                        args.slots,
                        program_id=args.program or "",
                        n_workers=args.workers,
                    )
                    & reactive_stats(Ledger)
                )
                >> (
                    nu.Log("--- sync report ---")
                    >> nu_virtuals.Snapshot(
                        nu.Log(
                            "txs synced",
                            nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "synced")),
                        )
                        >> nu.Log(
                            "txs skipped",
                            nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "skipped")),
                        )
                    )
                )
            )

            # Archive phase
            app = nm.inline_refs(app)
            app = nu_virtuals.inline_refs(app)
            app = nu_virtuals.auto_atomic(app)
            app = nu_inspect.set_logger_name(app, "sol")

            await runtime.aexecute(app, ctx, max_parallel=args.max_parallel)

            # Read phase
            app = nu.Print(
                nu_virtuals.Snapshot(
                    Ledger.txs[
                        nu.Last(
                            nu.Filter(
                                nu.Iter(Ledger.txs.keys()),
                                condition=Ledger.txs[nu.StrAttrRef("item")].meta.fee > 100_000,
                            ),
                        )
                    ].extract()
                )
            )

            app = nm.inline_refs(app)
            app = nu_virtuals.inline_refs(app)
            app = nu_virtuals.auto_atomic(app)
            app = nu_inspect.set_logger_name(app, "sol")
            runtime.execute(app, ctx)

            await nudle.arun_ui(Ledger, ctx)


if __name__ == "__main__":
    asyncio.run(main())
