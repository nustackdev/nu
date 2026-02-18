"""Solana slot tracker — Ref + PV with reactive terminal output.

Polls Solana mainnet for the current slot, persists to PV storage,
tracks poll stats, reacts to slot changes on terminal.

Uses:
  Ref + method   → Solana JSON-RPC client
  everypv        → slot data (persistent, observable)
  everybase.abc  → flows (Seq, ForRange, Race, Delay, Print)
  everyshape     → reactive flows (ReactWhile)
"""

from __future__ import annotations

import asyncio

import httpx

import everypv as pv
from everybase import Context
from everybase.abc import DictValue, IntValue, method
from everybase.abc.flows import Delay, ForRange, Print, Race, Seq
from everybase.core import Ref
from everyshape import Shape
from everyshape.flows import ReactWhile


# ---- Solana RPC ----

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaClient:
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


class SolanaRef(Ref[SolanaClient]):
    """Ref that resolves a SolanaClient from context."""

    async def resolve(self, ctx: Context) -> str:
        return "solana"

    async def fetch(self, ctx: Context) -> SolanaClient:
        return ctx.get(SolanaClient)


class Solana(SolanaRef):
    get_slot = method(IntValue, "getSlot")
    get_latest_blockhash = method(DictValue, "getLatestBlockhash")


# ---- Shapes ----


class SlotData(Shape):
    """Slot tracking (PV — persistent, observable)."""

    current = pv.IntRef.slot()
    previous = pv.IntRef.slot()


class Stats(Shape):
    """Poll counters (PV)."""

    polls = pv.IntRef.slot()


# ---- Config ----

N_POLLS = 10
POLL_INTERVAL = 2.0


# ---- Tree ----

tracker = Seq(
    # Seed
    SlotData.current.set(Solana.get_slot()),
    SlotData.previous.set(SlotData.current),
    Stats.polls.set(1),
    Print("start slot", SlotData.current),
    # Poll + react
    Race(
        # Producer: poll slot in a loop
        ForRange(
            0,
            N_POLLS - 1,
            Seq(
                Delay(POLL_INTERVAL),
                SlotData.previous.set(SlotData.current),
                SlotData.current.set(Solana.get_slot()),
                Stats.polls.set(Stats.polls + 1),
            ),
        ),
        # Consumer: react to slot changes
        ReactWhile(
            SlotData.current.on_change(),
            Stats.polls < N_POLLS,
            Print("slot", SlotData.current, "delta", SlotData.current - SlotData.previous),
        ),
    ),
    # Final report
    Print("final slot", SlotData.current),
    Print("total polls", Stats.polls),
)


# ---- Run ----


async def main():
    from tkv.tkv.storage import StorageProtocol

    from everypv.adapters.codecs import TextCodec as Codec
    from everypv.adapters.observers.in_memory import InMemoryObserver
    from everypv.adapters.storages.textdb import TextStorage as Storage

    # Init services
    client = SolanaClient()
    observer = InMemoryObserver(codec=Codec())
    storage = Storage(".db-trader", codec=Codec(), observer=observer)
    observer.connect()
    storage.open()

    # Create execution context
    ctx = Context().with_handle(SolanaClient, client).with_handle(StorageProtocol, storage)

    # Add tree extensions
    tree = pv.auto_atomic(tracker)

    # Execute
    await tree.execute(ctx)

    # Close services
    storage.close()
    observer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
