"""Sharded storage - two backends, one Shape, transparent routing.

Two in-memory storages split by user ID. Same Shape, same refs,
same flow. Context predicates route reads and writes to the
correct shard. The tree doesn't know about sharding.

    shard_az: user IDs starting with a-m
    shard_nz: user IDs starting with n-z

Both eb-dict and eb-virtuals examples side by side.
The eb-virtuals example includes reactive observers across shards.
"""

from __future__ import annotations

import asyncio

import nu_virtuals as ebv
from nu_dict import DictRef
from nu import Context
from nu.abc import Print, Seq
from nu.abc.flows import Delay, Race
from nu.shape import Shape
from nu.shape.flows import ReactForever


# =============================================================================
# eb-dict example
# =============================================================================


class Scores(Shape):
    users = DictRef.slot(int)


async def run_dict() -> None:
    print("--- eb-dict sharding ---")

    shard_az: dict = {}
    shard_nz: dict = {}

    ctx = (
        Context()
        .bind(shard_az, dict, Scores, routing=lambda site: len(site) > 1 and site[1][0] < "n")
        .bind(shard_nz, dict, Scores, routing=lambda site: len(site) > 1 and site[1][0] >= "n")
    )

    tree = Seq(
        Scores.users["alice"].store(95),
        Scores.users["bob"].store(82),
        Scores.users["nancy"].store(88),
        Scores.users["zara"].store(91),
        Print("alice", Scores.users["alice"]),
        Print("bob", Scores.users["bob"]),
        Print("nancy", Scores.users["nancy"]),
        Print("zara", Scores.users["zara"]),
    )
    await tree.execute(ctx)

    print(f"  shard a-m: {shard_az}")
    print(f"  shard n-z: {shard_nz}")
    assert "alice" in shard_az.get("users", {})
    assert "nancy" in shard_nz.get("users", {})
    print()


# =============================================================================
# eb-virtuals example: sharding + reactive observer
# =============================================================================


class Registry(Shape):
    users = ebv.DictRef.slot(value_type=int)


async def run_virtuals() -> None:
    print("--- eb-virtuals sharding + reactive ---")

    from virtuals import Navigator
    from virtuals.codecs import NoOpCodec
    from virtuals.observers.mem import InMemoryObserver
    from virtuals.storages.mem import InMemoryStorage

    codec = NoOpCodec()

    with (
        InMemoryObserver(codec=codec) as observer,
        InMemoryStorage(codec=codec, observer=observer) as storage_az,
        InMemoryStorage(codec=codec, observer=observer) as storage_nz,
    ):
        nav_az = Navigator(storage_az)
        nav_nz = Navigator(storage_nz)

        ctx = (
            Context()
            .bind(nav_az, Navigator, routing=lambda site, path: site[0][0] < "n")
            .bind(nav_nz, Navigator, routing=lambda site, path: site[0][0] >= "n")
        )

        # Producer: write users across shards in steps with delays.
        # Consumers: two reactive watchers, one on each shard,
        #   observing a specific user key per shard.
        # Race cancels consumers when the producer finishes.
        tree = ebv.auto_atomic(
            Seq(
                Race(
                    # Producer: write + update users across both shards
                    Seq(
                        Registry.users["alice"].store(90),
                        Delay(0.02),
                        Registry.users["nancy"].store(80),
                        Delay(0.02),
                        Registry.users["alice"].store(95),  # update on shard a-m
                        Delay(0.02),
                        Registry.users["nancy"].store(88),  # update on shard n-z
                        Delay(0.02),
                    ),
                    # Consumer: watch alice (shard a-m)
                    ReactForever(
                        Registry.users["alice"].on_change(),
                        Print("  [shard a-m] alice =", Registry.users["alice"]),
                    ),
                    # Consumer: watch nancy (shard n-z)
                    ReactForever(
                        Registry.users["nancy"].on_change(),
                        Print("  [shard n-z] nancy =", Registry.users["nancy"]),
                    ),
                    # Parent Consumer: watch all users
                    ReactForever(
                        Registry.users.on_change(),
                        Print("  changed user"),
                    ),
                ),
                # Final reads after all writes
                Print("alice", Registry.users["alice"]),
                Print("nancy", Registry.users["nancy"]),
            ),
        )
        await tree.execute(ctx)
    print()


# =============================================================================


async def main() -> None:
    await run_dict()
    await run_virtuals()
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
