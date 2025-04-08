from __future__ import annotations

from typing import TYPE_CHECKING

from .context import ServiceContext
from .types import ServiceRole

if TYPE_CHECKING:
    from loomi.service.base import Service, ServiceKey

__all__ = [
    "DependencyNode",
]


class DependencyNode:
    """
    Node in dependency graph tracking relationships and usage contexts.

    This class represents a service in the dependency graph, tracking both
    its relationships with other services and its usage context. It maintains
    bidirectional relationship information to support proper cleanup decisions.

    Attributes:
        service: The service this node represents
        context: Tracks service roles and usage
        dependencies: Named dependencies this service requires
        dependents: Services that depend on this service
        initiators: Keys of services that initiated relationships

    The distinction between dependents and initiators is important:
    - dependents tracks current relationships
    - initiators tracks historical relationship creation for cleanup
    """

    def __init__(self, service: "Service", is_dependency: bool) -> None:
        # The service this node represents
        self.service = service

        # Track service usage context
        self.context = ServiceContext(ServiceRole.DEPENDENCY if is_dependency else ServiceRole.ROOT)

        # Map of dependency name to service instance
        self.dependencies: dict[str, "Service"] = {}

        # Set of services that depend on this one
        self.dependents: set["Service"] = set()

        # Track which services initiated relationships (for cleanup)
        self.initiators: set["ServiceKey"] = set()

        # Track references of services (or root variables) that no longer use this service
        # This is used to determine if a service is orphaned and can be cleaned up
        self.detached_dependents: set["ServiceKey"] = set()

    def register_root(self) -> None:
        """
        Register a new root usage of this service.
        """
        self.context.add_role(ServiceRole.ROOT)

    def unregister_root(self) -> None:
        """
        Unregister a root usage of this service.
        """
        self.context.remove_role(ServiceRole.ROOT)

    def add_dependent(self, dependent: "Service") -> None:
        """
        Add a dependent service and update context.

        Updates both the relationship tracking and service context
        to reflect new dependency usage.

        Args:
            dependent: Service that depends on this one
        """
        self.dependents.add(dependent)
        self.initiators.add(dependent.key)
        self.context.add_role(ServiceRole.DEPENDENCY)

    def remove_dependent(self, dependent: "Service") -> None:
        """
        Remove a dependent service and update context.

        Updates both relationship tracking and service context
        when a dependency relationship ends.

        Args:
            dependent: Service to remove
        """
        self.dependents.discard(dependent)
        self.initiators.discard(dependent.key)
        self.context.remove_role(ServiceRole.DEPENDENCY)

    def add_dependency(self, name: str, dependency: "Service") -> None:
        """
        Record a named dependency relationship.

        Args:
            name: Name of dependency in parent service
            dependency: The dependent service
        """
        self.dependencies[name] = dependency

    def get_dependency(self, name: str) -> "Service | None":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to look up

        Returns:
            Dependency service or None if not found
        """
        return self.dependencies.get(name)

    def remove_dependency(self, name: str) -> "Service | None":
        """
        Remove and return named dependency if it exists.

        Args:
            name: Name of dependency to remove

        Returns:
            Removed service or None if not found
        """
        return self.dependencies.pop(name, None)

    def detach_dependent(self, service: "ServiceKey") -> None:
        """
        Detach a reference to this service.

        Args:
            service: Service key or root variable to detach
        """
        self.detached_dependents.add(service)

    def __repr__(self) -> str:
        return (
            "<DependencyNode: "
            f"\nservice={self.service.readable_name}, "
            f"\nservice_state={self.service.service_state}, "
            f"\nservice_key={self.service.key}, "
            f"\ndependencies_count={len(self.dependencies)}, "
            f"\ndependents_count={len(self.dependents)}, "
            f"\ndetached_dependents={len(self.detached_dependents)}, "
            f"\ncontext={self.context}), "
            "\n>"
        )
