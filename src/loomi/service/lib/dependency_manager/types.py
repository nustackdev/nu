from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

__all__ = [
    "ServiceRole",
    "DependencyMap",
    "DependentSet",
]

DependencyMap = dict[str, "Service"]
DependentSet = set["Service"]


class ServiceRole(Enum):
    """
    Defines valid roles a service can have in the system.

    A service can transition between roles during its lifecycle:
    - ROOT: Service created directly by application code
    - DEPENDENCY: Service created to fulfill another service's dependency

    Services can hold multiple roles simultaneously when they're used
    both directly and as dependencies.
    """

    ROOT = auto()  # Service was created directly
    DEPENDENCY = auto()  # Service was created as a dependency
