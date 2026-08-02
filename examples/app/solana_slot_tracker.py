"""Solana slot tracker -- in-tree fabric dispatch + virtuals + reactive output.

Polls Solana mainnet for the current slot from *inside* the Nu tree, tracks
it on virtuals storage, tracks poll stats, and reacts to slot changes on the
terminal.

Uses:
  Solana(FabricRef) -> the JSON-RPC client as a Nu fabric; ``Solana.slot()``
                       calls ``getSlot`` in-tree and yields a typed Int
  nu.virtuals        -> slot data (observable; ephemeral for this demo since
                        every run reseeds it)
  nu.flows           -> Sequential, ForRangeDo, Race, Delay
  nu.core.io.print   -> stdio fabric writes
  ReactWhile         -> reactive subscription driven by
                        ``SlotData.current.on_change()`` -- fires live off
                        the virtuals observer each time the producer writes
"""

from __future__ import annotations

import asyncio

import httpx

import nu
import nu.virtuals as v
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ---- Solana RPC ----

MAINNET = "https://api.mainnet-beta.solana.com"


class SolanaClient:
    def __init__(self, url: str = MAINNET) -> None:
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


class Solana(nu.FabricRef):
    """The SolanaClient as a Nu fabric; ``Solana.slot()`` calls getSlot in-tree."""

    fabric = SolanaClient

    slot = nu.method_query(nu.Int, "getSlot")


# ---- Shapes ----


class SlotData(nu.Shape):
    """Slot tracking (virtuals -- persistent, observable)."""

    current = v.IntRef.slot()
    previous = v.IntRef.slot()


class Stats(nu.Shape):
    """Poll counters (virtuals)."""

    polls = v.IntRef.slot()


# ---- Config ----

N_POLLS = 10
POLL_INTERVAL = 2.0


# ---- Tree ----
#
# The whole poll now lives in the tree: each step sleeps, calls getSlot on the
# bound Solana service, and advances the persistent shape. The RPC is an in-tree
# dispatch atom, so nothing is primed driver-side.


def build_tracker() -> object:
    """Kept as a function (not a module constant) so the module imports cleanly."""
    return nu.Sequential(
        # Seed
        SlotData.current.set(Solana.slot()),
        SlotData.previous.set(SlotData.current),
        Stats.polls.set(1),
        nu.print("start slot", SlotData.current),
        # Poll + react
        nu.Race(
            # Producer: sleep + fetch + advance, all in-tree
            nu.ForRangeDo(
                0,
                N_POLLS - 1,
                nu.Sequential(
                    nu.Delay(POLL_INTERVAL),
                    SlotData.previous.set(SlotData.current),
                    SlotData.current.set(Solana.slot()),
                    Stats.polls.set(Stats.polls + 1),
                ),
            ),
            # Consumer: react to slot changes
            nu.ReactWhile(
                SlotData.current.on_change(),
                Stats.polls < N_POLLS,
                nu.print(
                    "slot",
                    SlotData.current,
                    "delta",
                    SlotData.current - SlotData.previous,
                ),
            ),
        ),
        # Final report
        nu.print("final slot", SlotData.current),
        nu.print("total polls", Stats.polls),
    )


# ---- Run ----


async def main() -> None:
    client = SolanaClient()

    # Ephemeral: every run reseeds SlotData/Stats from scratch, so no on-disk
    # persistence is needed -- memory_storage keeps this on the virtuals
    # substrate (real observer, real .on_change()) without a backend.
    with v.memory_storage() as storage:
        nav = Navigator(storage)
        with storage.transaction() as tx:
            ctx = (
                nu.Context()
                .bind(Navigator, nav)
                .bind(TransactionProtocol, tx)
                .bind(SolanaClient, client)
            )
            tree = v.tree.auto_flow_atomic(build_tracker())
            await nu.arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
