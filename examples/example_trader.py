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
from everybase.abc import DictValue, IntValue, TypeBase, ValueBase, method
from everybase.abc.flows import Delay, ForRange, Print, Race, Seq
from everyshape import Shape
from everyshape.flows import ReactWhile


# ---- Solana RPC ----

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaClient:
    def __init__(self, url: str = MAINNET):
        self._url = url
        self._id = 0

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

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


class SolanaType(TypeBase):
    """Solana RPC typed interface."""

    get_slot = method(IntValue, "getSlot")
    get_latest_blockhash = method(DictValue, "getLatestBlockhash")


class SolanaValue(SolanaType, ValueBase):
    """Computed Value."""


class SolanaRef(pv.ItemRef[SolanaClient, SolanaValue], SolanaType):
    """Ref that resolves a SolanaClient from PV storage."""

    def __init__(
        self,
        address: object,
        parent: object,
        owner_shape: type | None = None,
    ) -> None:
        super().__init__(address, SolanaClient, SolanaValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> SolanaRef:
        from everyshape import Slot

        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> SolanaValue:
        return SolanaValue(self)

    def set(self, value: object) -> SolanaValue:
        from everyshape import ItemSetCmd

        if isinstance(value, SolanaClient):
            val = SolanaValue(value)
        else:
            val = value
        return SolanaValue(ItemSetCmd(self, val))


# ---- Shapes ----


class Services(Shape):
    """External service handles (in-memory, ephemeral)."""

    solana = SolanaRef.slot()


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
    Services.solana.set(SolanaClient()),
    SlotData.current.set(Services.solana.get_slot()),
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
                SlotData.current.set(Services.solana.get_slot()),
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

    from everypv.adapters.storage import memory_storage, text_storage

    with text_storage(".db-trader") as data_store:
        with memory_storage() as service_store:
            ctx = (
                Context()
                .with_handle(StorageProtocol, data_store)
                .with_handle(StorageProtocol, service_store, scope=Services)
            )

            tree = pv.auto_atomic(tracker, scope=Services)
            tree = pv.auto_atomic(tree)
            await tree.execute(ctx)


if __name__ == "__main__":
    asyncio.run(main())
