"""
Base service functionality shared between async and sync services.

This module provides the common foundation for all service types through
the ServiceCommonBase class. It implements core service features including:
- Service specification management
- Identity and equality handling
- Name and key generation
- Registry and dependency manager integration

The functionality here is inherited by both async and sync service base classes
to ensure consistent behavior across all service types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from loomi._lib.spec import Spec

from .exceptions import SpecError
from .logger import logger
from .types import ServiceKey

if TYPE_CHECKING:
    from loomi._lib.dependency_manager import DependencyManager
    from loomi._lib.service_registry import ServiceRegistry


__all__ = [
    "ServiceCommon",
]


class ServiceCommon:
    """
    Base class providing common functionality for all service types.

    This class implements the core features needed by all services, whether
    async or sync. It handles service specifications, identity management,
    registry integration, and basic service properties.

    Class Attributes:
        _registry (ServiceRegistry): Shared service registry for instance tracking
        _dep_manager (DependencyManager): Shared dependency manager for service relationships

    Attributes:
        _spec (Spec): Service specification defining the instance's properties

    Properties:
        spec (Spec): Access to the service specification
        name (str): Service instance name
        readable_name (str): Human-readable service identifier
        key (ServiceKey): Unique service instance identifier
    """

    _registry: ClassVar["ServiceRegistry"]
    _dep_manager: ClassVar["DependencyManager"]

    @classmethod
    def factory_name(cls) -> str:
        """
        Get the fully qualified name of the service class.

        Returns:
            str: String in format "module.ClassName"
        """
        return f"{cls.__module__}.{cls.__name__}"

    def __init__(self, spec: Spec | None = None) -> None:
        """
        Initialize a new service instance.

        Args:
            spec: Service specification defining instance properties. If None,
                 a default spec will be created using the class as factory.

        Raises:
            SpecError: If spec is invalid (wrong type or wrong factory)

        Notes:
            - Validates spec type and factory if provided
            - Creates default spec if none provided
            - Logs initialization details at appropriate levels
        """
        if spec is not None and not isinstance(spec, Spec):
            logger.error(f"Expected type matching SpecProtocol, got '{type(spec)}'")
            raise SpecError(f"Expected type matching SpecProtocol, got '{type(spec)}'")

        if spec is not None and spec.factory is not self.__class__:
            logger.error(f"Expected spec factory '{self.factory_name()}', got {spec.factory}")
            raise SpecError(f"Expected spec factory '{self.factory_name()}', got {spec.factory}")

        if spec is None:
            spec = Spec(factory=self.__class__, name="")
            logger.warning(f"Initializing '{self.factory_name()}' with base spec: {spec}")

        self._spec = spec
        logger.debug(f"Initialized service '{self.readable_name}' with spec {spec}")

    @property
    def spec(self) -> Spec:
        """
        Get the service's specification.

        Returns:
            Spec: The specification defining this service instance
        """
        return self._spec

    @property
    def name(self) -> str:
        """
        Get the service instance name.

        Returns:
            str: Name defined in the service specification
        """
        return self.spec.name

    @property
    def readable_name(self) -> str:
        """
        Get a human-readable identifier for the service.

        Returns:
            str: String combining name (if present) and class name
        """
        return ((self.spec.name + ":") if self.spec.name else "") + f"{self.__class__.__name__}"

    @property
    def key(self) -> ServiceKey:
        """
        Get the unique service instance identifier.

        Returns:
            ServiceKey: Unique key generated from the specification
        """
        return ServiceKey(self.spec.key)

    def __hash__(self) -> int:
        """
        Generate hash based on service key.

        Returns:
            int: Hash value for the service instance
        """
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """
        Compare service instances based on their keys.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is same service type with matching key
        """
        if other is None:
            return False
        return isinstance(other, type(self)) and self.key == other.key

    def __repr__(self) -> str:
        """
        Generate string representation of the service.

        Returns:
            str: Human-readable string showing service name and spec
        """
        return f"<Service '{self.readable_name}': spec=({self.spec})>"
