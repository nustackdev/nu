"""Solana slot tracker -- external service + virtuals with reactive terminal output.

Polls Solana mainnet for the current slot, persists to virtuals storage,
tracks poll stats, reacts to slot changes on terminal.

Uses:
  ServiceRef        -> Solana JSON-RPC client bound on the Context
  nu.virtuals       -> slot data (persistent, observable)
  nu.flows          -> Sequential, ForRangeDo, Race, DelayedDo
  nu.core.io.print  -> stdio fabric writes
  ReactWhile        -> reactive subscription (virtuals-side reactivity is
                       deferred, so the react branch is a placeholder today)

FIXME: the old typed-method-descriptor system (``method(IntI, "getSlot")``,
``TypeBase``/``Interface``) is gone. This example wires the RPC calls as raw
Python coroutines executed from the driver, then feeds the results into the Nu
tree via attrs. Revisit once a typed-RPC dispatch surface lands.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import httpx

import nu.virtuals as v
from nu import Context, arun
from nu.context import IntAttrRef, ServiceRef
from nu.core import Noop
from nu.core.io import print as nu_print
from nu.domains.shape import Shape
from nu.flows import DelayedDo, ForRangeDo, ReactWhile, Race, Sequential
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


# ---- Helpers ----


async def _fetch_slot(ctx: Context) -> int:
    """Pull the current slot off the bound SolanaClient service and stash it."""
    client = ctx.get(SolanaClient)
    slot = int(await client.getSlot())
    ctx.attrs["fetched_slot"] = slot
    return slot


# ---- Tree ----
#
# The pattern: the driver primes ctx.attrs["fetched_slot"] with a fresh slot
# before each Nu step, and the Nu tree copies it into the persistent shape and
# reacts to the change. Once the RPC dispatch story returns to Nu, the fetch
# call moves back inside the tree.


def build_tracker() -> object:
    """Kept as a function so the module imports even when virtuals reactivity is off."""
    return Sequential(
        # Seed
        SlotData.current.store(IntAttrRef("fetched_slot")),
        SlotData.previous.store(SlotData.current),
        Stats.polls.store(1),
        nu_print("start slot", SlotData.current),
        # Poll + react
        Race(
            # Producer: sleep + advance (fetch happens driver-side, see main())
            ForRangeDo(
                0,
                N_POLLS - 1,
                Sequential(
                    DelayedDo(POLL_INTERVAL, Noop()),
                    SlotData.previous.store(SlotData.current),
                    SlotData.current.store(IntAttrRef("fetched_slot")),
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
                # Prime the first slot then run the tree.
                await _fetch_slot(ctx)
                tree = v.auto_atomic(build_tracker())
                await arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
