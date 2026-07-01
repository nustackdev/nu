"""eb-distributed: distributed execution adapters for everybase.

Provides composables Resources for:
- Storage (InMemory, RocksDB, Text) + Codec + Observer (InMemory, Redis)
- Navigator (virtuals entrypoint)
- Context + Worker (tree execution)
- Invisibles (server + client for transparent proxying)
- Ray (actors + workers on Ray nodes)
- Teleport (span that ships subtrees to workers)

On import, registers everybase Nu and composables Spec as
value types in invisibles. This means trees and specs fly through
invisibles by value automatically (no manual serialization needed).
"""

from composables.spec import BaseSpec
from invisibles import register_value_type
from nu.lang import Nu

from .meta import auto_distribute
from .resources import (
    CodecResource,
    CodecSpec,
    ContextResource,
    ContextSpec,
    InMemoryObserverResource,
    InMemoryObserverSpec,
    InMemoryStorageResource,
    InMemoryStorageSpec,
    InvisiblesClient,
    InvisiblesClientSpec,
    InvisiblesServer,
    InvisiblesServerSpec,
    InvisiblesWorker,
    InvisiblesWorkerServer,
    InvisiblesWorkerServerSpec,
    InvisiblesWorkerSpec,
    NavigatorResource,
    NavigatorSpec,
    RayActor,
    RayActorSpec,
    RayWorker,
    RayWorkerSpec,
    RedisObserverResource,
    RedisObserverSpec,
    RocksDBStorageResource,
    RocksDBStorageSpec,
    TextStorageResource,
    TextStorageSpec,
    Worker,
    WorkerSpec,
    binary_codec_spec,
    msgpack_codec_spec,
    noop_codec_spec,
    text_codec_spec,
)
from .spans import Teleport


# Register value types: trees and specs serialize by value through invisibles.
# No lifecycle, immutable, safe to send as data.
register_value_type(Nu, BaseSpec)


__all__ = [
    "CodecResource",
    "CodecSpec",
    "ContextResource",
    "ContextSpec",
    "InMemoryObserverResource",
    "InMemoryObserverSpec",
    "InMemoryStorageResource",
    "InMemoryStorageSpec",
    "InvisiblesClient",
    "InvisiblesClientSpec",
    "InvisiblesServer",
    "InvisiblesServerSpec",
    "InvisiblesWorker",
    "InvisiblesWorkerServer",
    "InvisiblesWorkerServerSpec",
    "InvisiblesWorkerSpec",
    "NavigatorResource",
    "NavigatorSpec",
    "RayActor",
    "RayActorSpec",
    "RayWorker",
    "RayWorkerSpec",
    "RedisObserverResource",
    "RedisObserverSpec",
    "RocksDBStorageResource",
    "RocksDBStorageSpec",
    "Teleport",
    "TextStorageResource",
    "TextStorageSpec",
    "Worker",
    "WorkerSpec",
    "auto_distribute",
    "binary_codec_spec",
    "msgpack_codec_spec",
    "noop_codec_spec",
    "text_codec_spec",
]
