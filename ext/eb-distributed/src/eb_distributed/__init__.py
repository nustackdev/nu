"""eb-distributed: distributed execution adapters for everybase.

Provides composables Resources for:
- Invisibles RPC (server + client for transparent proxying)
- Ray actors (generic composables Resource host on Ray nodes)
- Worker (executes trees against its own Context)
- Teleport (Span that ships subtrees to Workers)

On import, registers everybase Executable and composables Spec as
value types in invisibles. This means trees and specs fly through
RPC by value automatically (no manual serialization needed).
"""

from composables.spec import BaseSpec
from invisibles import register_value_type

from everybase.core.executable import Executable

from .context import ContextResource, ContextSpec
from .presets import local
from .ray import RayActor, RayActorSpec, RayWorker, RayWorkerSpec
from .ray.presets import distributed
from .rpc.client import InvisiblesClient, InvisiblesClientSpec
from .rpc.server import InvisiblesServer, InvisiblesServerSpec
from .storage import (
    CodecResource,
    CodecSpec,
    InMemoryStorageResource,
    InMemoryStorageSpec,
    NavigatorResource,
    NavigatorSpec,
    RocksDBStorageResource,
    RocksDBStorageSpec,
)
from .teleport import Teleport
from .worker import Worker, WorkerSpec


# Register value types: trees and specs serialize by value through RPC.
# No lifecycle, immutable, safe to send as data.
register_value_type(Executable, BaseSpec)


__all__ = [  # noqa: RUF022
    # Ray
    "RayActor",
    "RayActorSpec",
    "RayWorker",
    "RayWorkerSpec",
    "distributed",
    # Storage
    "CodecResource",
    "CodecSpec",
    "ContextResource",
    "ContextSpec",
    "InMemoryStorageResource",
    "InMemoryStorageSpec",
    "NavigatorResource",
    "NavigatorSpec",
    "RocksDBStorageResource",
    "RocksDBStorageSpec",
    # RPC
    "InvisiblesClient",
    "InvisiblesClientSpec",
    "InvisiblesServer",
    "InvisiblesServerSpec",
    # Core
    "Teleport",
    "Worker",
    "WorkerSpec",
    # Presets
    "local",
]
