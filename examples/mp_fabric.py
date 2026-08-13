"""nu.mp as a Nu compute fabric."""

import os

import nu


# =========================================================================
# 1. Singleton: Provide + untagged Teleport
# =========================================================================


def demo_singleton() -> None:
    print("=" * 60)
    print(f"1. Provide: one untagged worker (driver pid={os.getpid()})")
    print("=" * 60)

    tree = nu.Provide(
        nu.mp.MpWorker,
        {"name": "solo"},
        nu.mp.Teleport(nu.Add(41, 1)),
    )
    result, _ = nu.run(tree)
    print(f"  yield: {result}")


# =========================================================================
# 2. Fleet by index tag: ProvideList + integer targets
# =========================================================================


def demo_fleet_by_index() -> None:
    print("=" * 60)
    print("2. ProvideList: 3 workers keyed 0, 1, 2")
    print("=" * 60)

    tree = nu.ProvideList(
        nu.mp.MpWorker,
        [
            {"name": "worker-0"},
            {"name": "worker-1"},
            {"name": "worker-2"},
        ],
        nu.Add(
            nu.mp.Teleport(nu.Add(1, 2), target=0),  # 3
            nu.mp.Teleport(nu.Add(10, 20), target=1),  # 30
            nu.mp.Teleport(nu.Add(100, 200), target=2),  # 300
        ),
    )
    result, _ = nu.run(tree)
    print(f"  yield: {result}")


# =========================================================================
# 3. Keyed fleet: ProvideDict with tuple + string tags
# =========================================================================


def demo_keyed_fleet() -> None:
    print("=" * 60)
    print("3. ProvideDict: ('shard', 0), ('shard', 1), 'indexer-main'")
    print("=" * 60)

    tree = nu.ProvideDict(
        nu.mp.MpWorker,
        {
            ("shard", 0): {"name": "shard-0"},
            ("shard", 1): {"name": "shard-1"},
            "indexer-main": {"name": "indexer-main"},
        },
        nu.Add(
            nu.mp.Teleport(nu.Add(1, 2), target=("shard", 0)),  # 3
            nu.mp.Teleport(nu.Add(3, 4), target=("shard", 1)),  # 7
            nu.mp.Teleport(nu.Add(5, 6), target="indexer-main"),  # 11
        ),
    )
    result, _ = nu.run(tree)
    print(f"  yield: {result}")


if __name__ == "__main__":
    demo_singleton()
    demo_fleet_by_index()
    demo_keyed_fleet()
