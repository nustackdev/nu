"""Solana slot tracker — service + PV + dict with reactive terminal output.

Polls Solana mainnet for the current slot, persists to PV storage,
tracks poll stats in memory, reacts to slot changes on terminal.

Substrates:
  eb-service  → Solana JSON-RPC client
  eb-pv       → slot data (persistent, observable)
  eb-dict     → poll counters (ephemeral)
"""

from __future__ import annotations

import asyncio

import httpx

import eb_dict as mem
import eb_flow as f
import eb_pv as pv
from eb_service import Service
from eb_shape import Shape
from everybase import Context
from everybase.abc import DictValue, IntValue, method


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


class Solana(Service):
    SERVICE_CLS = SolanaClient

    get_slot = method(IntValue, "getSlot")
    get_latest_blockhash = method(DictValue, "getLatestBlockhash")


# ---- Shapes ----


class SlotData(Shape):
    """Slot tracking (PV — persistent, observable)."""

    current = pv.IntRef.slot()
    previous = pv.IntRef.slot()


class Stats(Shape):
    """Poll counters (dict — ephemeral)."""

    polls = mem.IntRef.slot()


# ---- Config ----

N_POLLS = 10
POLL_INTERVAL = 2.0


# ---- Tree ----

tracker = f.Seq(
    # Seed
    SlotData.current.set(Solana.get_slot()),
    SlotData.previous.set(SlotData.current),
    Stats.polls.set(1),
    f.Print("start slot", SlotData.current),
    # Poll + react
    f.Race(
        # Producer: poll slot in a loop
        f.ForRange(
            0,
            N_POLLS - 1,
            f.Seq(
                f.Delay(POLL_INTERVAL),
                SlotData.previous.set(SlotData.current),
                SlotData.current.set(Solana.get_slot()),
                Stats.polls.set(Stats.polls + 1),
            ),
        ),
        # Consumer: react to slot changes
        f.ReactWhile(
            SlotData.current.on_change(),
            Stats.polls < N_POLLS,
            f.Print("slot", SlotData.current, "delta", SlotData.current - SlotData.previous),
        ),
    ),
    # Final report
    f.Print("final slot", SlotData.current),
    f.Print("total polls", Stats.polls),
)


# ---- Run ----


async def main():
    from tkv.tkv.storage import StorageProtocol

    from eb_pv.adapters.codecs import TextCodec as Codec
    from eb_pv.adapters.observers.in_memory import InMemoryObserver
    from eb_pv.adapters.storages.textdb import TextStorage as Storage
    from eb_pv.views import DictView

    # Init services
    client = SolanaClient()
    counters: dict = {}
    observer = InMemoryObserver(codec=Codec())
    storage = Storage(".db-trader", codec=Codec(), observer=observer)
    observer.connect()
    storage.open()

    # Create execution context
    ctx = (
        Context()
        .with_handle(SolanaClient, client)
        .with_handle(dict, counters, shape=Stats)
        .with_handle(StorageProtocol, storage, shape=SlotData)
    )

    # Add tree extensions
    tree = pv.auto_atomic(tracker, SlotData, DictView)
    # ...

    # Execute
    await tree.execute(ctx)

    # Close services
    storage.close()
    observer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
