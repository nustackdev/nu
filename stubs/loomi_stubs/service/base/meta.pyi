from abc import ABCMeta
from typing import Any, Generic, TypeVar

from loomi.service.lib.dependency_manager import DependencyManager
from loomi.service.lib.service_registry import ServiceRegistry

from .bases import Service
from .spec import Spec

__all__ = ["ServiceMeta"]

ServiceT = TypeVar("ServiceT", bound="Service")
FeatureT = TypeVar("FeatureT")

class ServiceMeta(ABCMeta, Generic[ServiceT]):
    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **features: Any
    ) -> type[ServiceT]: ...
    def __call__(cls, spec: Spec | None = None, /, *args: Any, **kwargs: Any) -> ServiceT: ...
    @property
    def registry(cls) -> ServiceRegistry: ...
    @property
    def dep_manager(cls) -> DependencyManager: ...
