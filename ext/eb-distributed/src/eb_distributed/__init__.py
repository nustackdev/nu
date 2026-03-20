"""eb-distributed: distributed execution adapters for everybase.

Provides composables Resources for:
- Invisibles RPC (server + client)
- Process launching (multiprocessing)
"""

from .launcher.process import ProcessLauncher, ProcessLauncherSpec
from .rpc.client import InvisiblesClient, InvisiblesClientSpec
from .rpc.server import InvisiblesServer, InvisiblesServerSpec


__all__ = [
    "InvisiblesClient",
    "InvisiblesClientSpec",
    "InvisiblesServer",
    "InvisiblesServerSpec",
    "ProcessLauncher",
    "ProcessLauncherSpec",
]
