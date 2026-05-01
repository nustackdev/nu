#!/usr/bin/env python3
# ruff: noqa: N815
"""Solana block archive - fetch blocks, persist transactions as-is.

Shape attrs mirror the JSON-RPC `getBlock` field names verbatim
(``accountKeys``, ``preBalances``, ...) so blocks/txs round-trip without
key translation. N815 (mixedCase class scope) is silenced for this file.

Usage:
    python examples/solana_block_archive.py --slot-from 408000000 --slots 20
"""

import argparse
import asyncio
import logging
from functools import reduce
from operator import or_

import aiohttp

import nu
import nu_inspect
import nu_mem as nm
import nu_virtuals as nv
import nudle
import virtuals


class DroppedSlotError(Exception):
    pass


# -- Client -------------------------------------------------------------------


class SolanaRpc:
    """Minimal async Solana JSON-RPC client. Returns raw `result` payload."""

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._session: aiohttp.ClientSession | None = None
        self._id = 0

    async def _call(self, method: str, params: list | None = None) -> object:
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
        """Fetch block; return {"slot": slot, "block": <raw result>}."""
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


class SolanaRef(nu.Ref[SolanaRpc]):
    support = frozenset({nu.Mode.SYNC, nu.Mode.ASYNC})

    def eval(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    async def aeval(self, ctx: nu.Context) -> SolanaRpc:
        return ctx.get(SolanaRpc)

    get_block = nu.Invocation(nu.DictForm, "get_block", support=frozenset({nu.Mode.ASYNC}))


# -- Shapes -------------------------------------------------------------------


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
    """One fetch branch.
    Strides by n_workers, pulls each block, appends the raw entry to _RangeScratch.blocks.
    On drop: log + skip.
    """

    slot = nu.IntAttrRef(f"slot_{worker_id}")

    return nu.ForRangeDo(
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

    slot = nu.IntForm(nu.DictForm(entry_ref)["slot"])

    return (
        ledger.blocks_meta[slot].skipped.init(0)
        >> ledger.blocks_meta[slot].synced.init(0)
        >> _SlotScratch.tx_idx.store(0)
        >> nv.Transaction(
            nu.ForEachDo(
                nu.DictForm(nu.DictForm(entry_ref)["block"])["transactions"],
                nu.IfDo(
                    nu.ToBool(program_id),
                    nu.IfDo(
                        nu.Contains(
                            nu.DictForm(
                                nu.DictForm(nu.DictAttrRef("tx")["transaction"])["message"]
                            )["accountKeys"],
                            program_id,
                        ),
                        ledger.blocks_meta[slot].synced.inc() >> _persist_tx(ledger, slot),
                        # ledger.blocks_meta[slot].skipped.inc(),
                    ),
                    ledger.blocks_meta[slot].synced.inc() >> _persist_tx(ledger, slot),
                ),
                item="tx",
            )
        )
        >> ledger.slots_synced.add(slot)
    )


def processor(ledger: type[Ledger], *, program_id: nu.StrArg = "") -> nu.Nu:
    """Sync consumer.

    Polls _RangeScratch.blocks at cursor, persists, increments cursor, sleeps.
    Terminates when fetchers finish (fetch_done) and the buffer is fully drained.
    """

    entry = _RangeScratch.blocks[_RangeScratch.cursor]

    return nu.WhileDo(
        nu.or_(
            ledger.fetch_done.not_(),
            _RangeScratch.cursor < nu.Len(_RangeScratch.blocks),
        ),
        nu.IfDo(
            _RangeScratch.cursor < nu.Len(_RangeScratch.blocks),
            process_entry(ledger, entry, program_id=program_id) >> _RangeScratch.cursor.inc(),
            nu.stdlib.TimeSleep(0.05),
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
    """Sync slot_count slots starting at slot_from.

    n_workers async fetchers stream blocks into _RangeScratch.blocks;
    one sync processor drains the list and persists each entry.

    Fetchers share the event loop; the processor runs on a worker thread. Needs max_parallel >= 2.
    """

    return (
        Ledger.slots_synced.init(set())
        >> Ledger.slots_dropped.init(set())
        >> _RangeScratch.blocks.store([])
        >> _RangeScratch.cursor.init(0)
        >> nu.Log("sync:", slot_from, "->", slot_from + slot_count)
        >> (
            reduce(
                or_,
                (fetcher(ledger, slot_from, slot_count, i, n_workers) for i in range(n_workers)),
            )
            >> Ledger.fetch_done.store(True)
            | processor(ledger, program_id=program_id)
        )
    )


def reactive_stats(ledger: type[Ledger]) -> nu.Nu:
    """Reactive observers: log block arrivals and per-block synced/skipped counters."""
    return (
        nu.shapes.ReactForever(
            ledger.blocks_meta.on_descendants_change("*"),
            nu.Log("new block:", nu.TupleAttrRef("slot_change")[-1]),
            changed_key="slot_change",
        )
        | nu.shapes.ReactForever(
            ledger.blocks_meta.on_descendants_change("*", "skipped"),
            nu.Throttle(
                0.2,
                nu.Log(
                    "block",
                    nu.TupleAttrRef("skipped_change")[-2],
                    "txs skipped:",
                    ledger.blocks_meta[nu.TupleAttrRef("skipped_change")[-2]].skipped,
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
                    nu.TupleAttrRef("synced_change")[-2],
                    "txs synced:",
                    ledger.blocks_meta[nu.TupleAttrRef("synced_change")[-2]].synced,
                ),
            ),
            changed_key="synced_change",
        )
    )


# -- Apps ---------------------------------------------------------------------


def archive_app(
    *,
    slot_from: int,
    slots: int,
    endpoint: str,
    db_path: str,
    program_id: str = "",
    n_workers: int = 6,
) -> nu.Nu:
    """Sync `slots` blocks from `slot_from` and persist matching txs."""
    return (
        (
            nu.Log("--- sync ---")
            >> nu.Log("syncing", slots, "slots from", slot_from)
            >> nu.Log("endpoint:", endpoint)
            >> nu.Log("filter: program", program_id or "(none)")
            >> nu.Log("db:", db_path)
            >> Ledger.fetch_done.store(False)
        )
        >> (
            sync_range(Ledger, slot_from, slots, program_id=program_id, n_workers=n_workers)
            & reactive_stats(Ledger)
        )
        >> (
            nu.Log("--- sync report ---")
            >> nv.Snapshot(
                nu.Log("txs synced", nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "synced")))
                >> nu.Log("txs skipped", nu.Sum(nu.Pluck(Ledger.blocks_meta.values(), "skipped")))
            )
        )
    )


def query_app(*, min_fee: int) -> nu.Nu:
    """Print the most recent persisted tx whose fee exceeds `min_fee`."""
    item = nu.StrAttrRef("item")
    return nu.Print(
        nv.Snapshot(
            Ledger.txs[
                nu.Last(
                    nu.Filter(
                        nu.Iter(Ledger.txs.keys()),
                        condition=Ledger.txs[item].meta.fee > min_fee,
                    ),
                )
            ].extract()  # type: ignore
        )
    )


# -- Main ---------------------------------------------------------------------


def prepare(app: nu.Nu, *, logger_name: str = "sol") -> nu.Nu:
    """Inline refs, wrap atomically, name the logger. Standard rewrite stack."""

    app = nm.inline_refs(app)
    app = nv.inline_refs(app)
    app = nv.auto_atomic(app)
    return nu_inspect.set_logger_name(app, logger_name)


def _setup_logging() -> None:
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("sol")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.propagate = False


def _parse_args() -> argparse.Namespace:
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
    return p.parse_args()


async def main() -> None:
    _setup_logging()
    args = _parse_args()

    rpc = SolanaRpc(endpoint=args.endpoint)
    with nv.rocksdb_storage_inmemory(args.db_path) as store:
        ctx = (
            nu.Context()
            .bind(virtuals.Navigator, virtuals.Navigator(store))
            .bind(SolanaRpc, rpc)
            .bind(dict, {})
        )

        archive = prepare(
            archive_app(
                slot_from=args.slot_from,
                slots=args.slots,
                endpoint=args.endpoint,
                db_path=args.db_path,
                program_id=args.program or "",
                n_workers=args.workers,
            )
        )
        query = prepare(query_app(min_fee=100_000))

        await nu.runtime.aexecute(archive, ctx, max_parallel=args.max_parallel)
        nu.runtime.execute(query, ctx)

        await nudle.arun_ui(Ledger, ctx)
        await rpc.close()


if __name__ == "__main__":
    asyncio.run(main())
