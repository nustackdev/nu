"""nu.ray - the ray compute fabric.

Ray reframes as a compute fabric: locations are actor processes, addresses
are tags, the interaction is ``Teleport`` (execute a Nu tree there).

- ``RayCluster`` - the cluster handle FabricLifecycle. On asetup ensures
  ray is initialized; on acleanup shuts down its own init (if any).
- ``RayService`` - one remote actor hosting a Nu ``Context`` + tree
  executor. Provisioned per-instance by ``Provide`` / ``ProvideList`` /
  ``ProvideDict``.
- ``RayClusterRef`` / ``RayServiceRef`` - fabric refs. ``RayServiceRef``
  takes an arbitrary hashable tag (``RayServiceRef("ledger-main")``,
  ``RayServiceRef(("ledger", 0))``).
- ``Teleport`` - the interaction; ships the body term to a tagged
  ``RayService`` and awaits its result.

Typical shape::

    Provide(RayCluster, {"address": "auto"},
        ProvideList(RayService, [
            {"actor_name": "worker-0", "num_cpus": 4},
            {"actor_name": "worker-1", "num_cpus": 4},
        ],
            Sequential(
                Teleport(some_tree, target=0),
                Teleport(some_tree, target=1),
            ),
        ),
    )
"""

from __future__ import annotations

from .interactions import Teleport
from .refs import RayClusterRef, RayServiceRef
from .resources import RayCluster, RayService


__all__ = [
    "RayCluster",
    "RayClusterRef",
    "RayService",
    "RayServiceRef",
    "Teleport",
]
