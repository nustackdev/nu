"""EveryFlow Distributed Launcher Package - Infrastructure provisioning for distributed resources.

This package provides launcher implementations that provision infrastructure
(processes, containers, Ray actors) and start hosts/servers within that
infrastructure. The hosts can then serve multiple resources when proxies
connect to them using connection information from launcher specifications.

Launchers are regular EveryFlow resources that handle infrastructure lifecycle
independently from proxy connections. Users create launchers to provision
infrastructure, then use connection information from specs to create proxies
that connect to the launched hosts.

Key Features:
    - Infrastructure-agnostic launcher base classes
    - Automatic provisioning and host startup via EveryFlow resource lifecycle
    - Clean separation between infrastructure management and resource access
    - Hosts can serve multiple resources as proxies connect
    - Simple specification-based configuration

Components:
    BaseLauncher: Abstract base class for launcher implementations
    BaseLauncherSpec: Specification for launcher configuration
    Exceptions: Launcher-specific error types
    Types: Common type definitions
"""

from __future__ import annotations

from .base import BaseLauncher, BaseLauncherSpec
from .exceptions import (
    LauncherConfigurationError,
    LauncherError,
    LauncherOperationError,
    LauncherProvisioningError,
)

# Types
from .types import ConnectionInfo, LauncherConfig


__all__ = [
    # Base components
    "BaseLauncher",
    "BaseLauncherSpec",
    # Exceptions
    "LauncherError",
    "LauncherConfigurationError",
    "LauncherOperationError",
    "LauncherProvisioningError",
    # Types
    "ConnectionInfo",
    "LauncherConfig",
]
