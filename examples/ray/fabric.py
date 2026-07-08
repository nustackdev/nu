"""Ray as a Nu compute fabric.

The whole Ray topology is described as a Nu tree: cluster provisioning, worker
fleet, remote execution. ``Provide`` / ``ProvideList`` / ``ProvideDict`` are
the DI system - each ``FabricLifecycle`` is constructed on entry, ``asetup``
runs, it binds on ctx, and teardown fires LIFO on exit.

Three shapes:

- ``Provide`` - one untagged singleton. ``Teleport`` with no target.
- ``ProvideList`` - fleet with integer index tags. ``Teleport(target=i)``.
- ``ProvideDict`` - mixed tuple + string tags, matching the citadel
  ``feed_run`` convention (``("ledger", 0)`` shards + a ``"ledger-main"``
  singleton). ``Teleport(target=("ledger", 0))``.

Each tree wraps its per-worker ``Teleport`` calls in an outer ``AddQuery`` -
the returned sum is what the whole tree yields, so no ``ctx.attrs`` gymnastics
around scoped-context semantics.

Run from the nu repo::

    ./.venv/bin/python examples/ray_fabric.py

Bypasses ``uv run`` because uv sets a project env that ray tries to package
as a runtime-env - the driver would then fail to install its own working
dir on the raylet. The example spawns a private local ray head in a
user-owned temp dir and tears it down at the end.
"""

from __future__ import annotations

import asyncio
import tempfile

from nu import arun
from nu.context import Provide, ProvideDict, ProvideList
from nu.core import AddQuery
from nu.ray import RayCluster, RayService, Teleport


# Local head config: spin up a private single-node cluster in a user-owned
# temp dir (the shared ``/tmp/ray`` belongs to the ark service user on this
# box). ``runtime_env={}`` skips the auto-package-cwd behavior that gets
# triggered when the driver runs inside a uv project.
_TMP = tempfile.mkdtemp(prefix="nu-ray-example-")
_CLUSTER_KWARGS = {
    "address": None,
    "_temp_dir": _TMP,
    "num_cpus": 4,
    "include_dashboard": False,
    "runtime_env": {},
}


# =========================================================================
# 1. Singleton: Provide + untagged Teleport
# =========================================================================


async def demo_singleton() -> None:
    print("=" * 60)
    print("1. Provide: one untagged service, Teleport with no target")
    print("=" * 60)

    tree = Provide(RayCluster, _CLUSTER_KWARGS,
        Provide(RayService, {"actor_name": "solo"},
            Teleport(AddQuery(41, 1)),
        ),
    )
    result, _ = await arun(tree)
    print(f"  yield: {result}")
    assert result == 42
    print("  PASS\n")


# =========================================================================
# 2. Fleet by index tag: ProvideList + integer targets
# =========================================================================


async def demo_fleet_by_index() -> None:
    print("=" * 60)
    print("2. ProvideList: 3 workers keyed 0, 1, 2")
    print("=" * 60)

    tree = Provide(RayCluster, _CLUSTER_KWARGS,
        ProvideList(RayService, [
            {"actor_name": "worker-0"},
            {"actor_name": "worker-1"},
            {"actor_name": "worker-2"},
        ],
            AddQuery(
                Teleport(AddQuery(1, 2), target=0),      # 3
                Teleport(AddQuery(10, 20), target=1),    # 30
                Teleport(AddQuery(100, 200), target=2),  # 300
            ),
        ),
    )
    result, _ = await arun(tree)
    print(f"  yield: {result}  (expect 333)")
    assert result == 333
    print("  PASS\n")


# =========================================================================
# 3. Keyed fleet: ProvideDict with tuple tags (feed_run shape) + singleton
# =========================================================================


async def demo_keyed_fleet() -> None:
    print("=" * 60)
    print("3. ProvideDict: ('ledger', 0), ('ledger', 1), 'ledger-main'")
    print("=" * 60)

    tree = Provide(RayCluster, _CLUSTER_KWARGS,
        ProvideDict(RayService, {
            ("ledger", 0):  {"actor_name": "ledger-0"},
            ("ledger", 1):  {"actor_name": "ledger-1"},
            "ledger-main":  {"actor_name": "ledger-main"},
        },
            AddQuery(
                Teleport(AddQuery(1, 2), target=("ledger", 0)),   # 3
                Teleport(AddQuery(3, 4), target=("ledger", 1)),   # 7
                Teleport(AddQuery(5, 6), target="ledger-main"),   # 11
            ),
        ),
    )
    result, _ = await arun(tree)
    print(f"  yield: {result}  (expect 21)")
    assert result == 21
    print("  PASS\n")


# =========================================================================
# main
# =========================================================================


async def main() -> None:
    await demo_singleton()
    await demo_fleet_by_index()
    await demo_keyed_fleet()
    print("=" * 60)
    print("ALL RAY FABRIC PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
