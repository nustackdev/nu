"""Solana slot tracker -- in-tree service dispatch + virtuals + reactive output.

Polls Solana mainnet for the current slot from *inside* the Nu tree, persists to
virtuals storage, tracks poll stats, and reacts to slot changes on the terminal.

Uses:
  Solana(ServiceRef) -> the JSON-RPC client as a Nu service; ``Solana.slot()``
                        calls ``getSlot`` in-tree and yields a typed IntForm
  nu.virtuals        -> slot data (persistent, observable)
  nu.flows           -> Sequential, ForRangeDo, Race, Delay
  nu.core.io.print   -> stdio fabric writes
  ReactWhile         -> reactive subscription (virtuals-side reactivity is
                        deferred, so the react branch is a placeholder today)
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import httpx

import nu.virtuals as v
from nu import Context, IntForm, arun
from nu.context import ServiceRef, method_query
from nu.core.io import print as nu_print
from nu.domains.shape import Shape
from nu.flows import Delay, ForRangeDo, Race, ReactWhile, Sequential
from nu.virtuals.presets import text_storage
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


class Solana(ServiceRef):
    """The SolanaClient as a Nu service; ``Solana.slot()`` calls getSlot in-tree."""

    service = SolanaClient

    slot = method_query(IntForm, "getSlot")


# ---- Shapes ----


class SlotData(Shape):
    """Slot tracking (virtuals -- persistent, observable)."""

    current = v.IntRef.slot()
    previous = v.IntRef.slot()


class Stats(Shape):
    """Poll counters (virtuals)."""

    polls = v.IntRef.slot()


# ---- Config ----

N_POLLS = 10
POLL_INTERVAL = 2.0


# ---- Tree ----
#
# The whole poll now lives in the tree: each step sleeps, calls getSlot on the
# bound Solana service, and advances the persistent shape. The RPC is a Nu
# InvokeAction, so nothing is primed driver-side.


def build_tracker() -> object:
    """Kept as a function so the module imports even when virtuals reactivity is off."""
    return Sequential(
        # Seed
        SlotData.current.store(Solana.slot()),
        SlotData.previous.store(SlotData.current),
        Stats.polls.store(1),
        nu_print("start slot", SlotData.current),
        # Poll + react
        Race(
            # Producer: sleep + fetch + advance, all in-tree
            ForRangeDo(
                0,
                N_POLLS - 1,
                Sequential(
                    Delay(POLL_INTERVAL),
                    SlotData.previous.store(SlotData.current),
                    SlotData.current.store(Solana.slot()),
                    Stats.polls.store(Stats.polls + 1),
                ),
            ),
            # Consumer: react to slot changes (see NOTE at top -- deferred)
            ReactWhile(
                SlotData.current.on_change(),  # FIXME: virtuals reactivity deferred
                Stats.polls < N_POLLS,
                nu_print(
                    "slot",
                    SlotData.current,
                    "delta",
                    SlotData.current - SlotData.previous,
                ),
            ),
        ),
        # Final report
        nu_print("final slot", SlotData.current),
        nu_print("total polls", Stats.polls),
    )


# ---- Run ----


async def main() -> None:
    client = SolanaClient()

    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "slots")
        with text_storage(db_path) as storage:
            nav = Navigator(storage)
            with storage.transaction() as tx:
                ctx = (
                    Context()
                    .bind(Navigator, nav)
                    .bind(TransactionProtocol, tx)
                    .bind(SolanaClient, client)
                )
                tree = v.auto_atomic(build_tracker())
                await arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
