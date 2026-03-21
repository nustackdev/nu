"""eb-distributed: distributed execution adapters for everybase.

Provides composables Resources for:
- Invisibles RPC (server + client)
- Process launching (multiprocessing)
"""

from .context import ContextResource, ContextSpec
from .launcher.process import ProcessLauncher, ProcessLauncherSpec
from .rpc.client import InvisiblesClient, InvisiblesClientSpec
from .rpc.server import InvisiblesServer, InvisiblesServerSpec
from .storage import (
    CodecResource,
    CodecSpec,
    InMemoryStorageResource,
    InMemoryStorageSpec,
    NavigatorResource,
    NavigatorSpec,
)


__all__ = [
    "CodecResource",
    "CodecSpec",
    "ContextResource",
    "ContextSpec",
    "InMemoryStorageResource",
    "InMemoryStorageSpec",
    "InvisiblesClient",
    "InvisiblesClientSpec",
    "InvisiblesServer",
    "InvisiblesServerSpec",
    "NavigatorResource",
    "NavigatorSpec",
    "ProcessLauncher",
    "ProcessLauncherSpec",
]
