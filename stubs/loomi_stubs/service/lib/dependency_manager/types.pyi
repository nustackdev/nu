from enum import Enum

from _typeshed import Incomplete

__all__ = ["ServiceRole", "DependencyMap", "DependentSet"]

DependencyMap: Incomplete
DependentSet: Incomplete

class ServiceRole(Enum):
    ROOT = ...
    DEPENDENCY = ...
