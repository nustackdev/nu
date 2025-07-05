from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

__all__ = [
    "ResourceRole",
]


class ResourceRole(Enum):
    """
    Defines valid roles a resource can have in the system.

    A resource can transition between roles during its lifecycle:
    - ROOT: Resource created directly by application code
    - DEPENDENCY: Resource created to fulfill another resource's dependency

    Resources can hold multiple roles simultaneously when they're used
    both directly and as dependencies.
    """

    ROOT = auto()  # Resource was created directly
    DEPENDENCY = auto()  # Resource was created as a dependency
