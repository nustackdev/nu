"""Launcher Specs - Process management utilities.

Provides utility functions for creating common launcher configurations
with sensible defaults for different deployment scenarios.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyflow.infra.launcher.multiprocessing import MultiprocessingLauncherSpec


if TYPE_CHECKING:
    from everylink import Spec


__all__ = [
    "get_launcher_spec",
]


def get_launcher_spec(
    host: Spec,
    launcher_type: str = "multiprocessing",
    name: str = "launcher",
) -> MultiprocessingLauncherSpec:
    """Create a launcher spec.

    Launches services in separate processes for isolation and parallelism.
    Ideal for CPU-bound workloads and service distribution.

    Args:
        launcher_type: Type of launcher to create (default "multiprocessing")
        host: Host specification for the launcher
        name: Optional name for the launcher


    Returns:
        MultiprocessingLauncherSpec configured for process management

    Examples:
        ```python
        # Basic multiprocessing launcher
        launcher = get_multiprocessing_launcher_spec(max_workers=8)

        # Launcher with RPyC server host
        server = get_rpyc_unix_server_spec("/tmp/service.sock")
        launcher = get_multiprocessing_launcher_spec(host=server, max_workers=4)

        # High-concurrency setup
        launcher = get_multiprocessing_launcher_spec(
            max_workers=16, name="high_concurrency_launcher"
        )
        ```
    """
    if launcher_type != "multiprocessing":
        raise ValueError(f"Unsupported launcher type: {launcher_type}")

    return MultiprocessingLauncherSpec(
        name=name,
        host=host,
    )
