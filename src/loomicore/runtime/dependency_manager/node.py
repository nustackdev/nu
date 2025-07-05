from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .context import ResourceContext
from .types import ResourceRole

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "DependencyNode",
]


class DependencyNode:
    """
    Node in dependency graph tracking relationships and usage contexts.

    This class represents a resource in the dependency graph, tracking both
    its relationships with other resources and its usage context. It maintains
    bidirectional relationship information to support proper cleanup decisions.

    Attributes:
        resource: The resource this node represents
        context: Tracks resource roles and usage
        dependencies: Named dependencies this resource requires
        dependents: Resources that depend on this resource
        initiators: Keys of resources that initiated relationships

    The distinction between dependents and initiators is important:
    - dependents tracks current relationships
    - initiators tracks historical relationship creation for cleanup
    """

    def __init__(self, resource: "Resource", is_dependency: bool) -> None:
        # The resource this node represents
        self.resource = resource

        # Track resource usage context
        self.context = ResourceContext(
            ResourceRole.DEPENDENCY if is_dependency else ResourceRole.ROOT
        )

        # Map of dependency name to resource instance
        self.dependencies: dict[str, "Resource"] = {}

        # Set of resources that depend on this one
        self.dependents: set["Resource"] = set()

        # Track which resources initiated relationships (for cleanup)
        self.initiators: set[str] = set()

        # Track references of resources (or root variables) that no longer use this resource
        # This is used to determine if a resource is orphaned and can be cleaned up
        self.detached_dependents: set[str] = set()

    def register_root(self) -> None:
        """
        Register a new root usage of this resource.
        """
        self.context.add_role(ResourceRole.ROOT)

    def unregister_root(self) -> None:
        """
        Unregister a root usage of this resource.
        """
        self.context.remove_role(ResourceRole.ROOT)

    def add_dependent(self, dependent: "Resource") -> None:
        """
        Add a dependent resource and update context.

        Updates both the relationship tracking and resource context
        to reflect new dependency usage.

        Args:
            dependent: Resource that depends on this one
        """
        self.dependents.add(dependent)
        self.initiators.add(dependent.key)
        self.context.add_role(ResourceRole.DEPENDENCY)

    def remove_dependent(self, dependent: "Resource") -> None:
        """
        Remove a dependent resource and update context.

        Updates both relationship tracking and resource context
        when a dependency relationship ends.

        Args:
            dependent: Resource to remove
        """
        self.dependents.discard(dependent)
        self.initiators.discard(dependent.key)
        self.context.remove_role(ResourceRole.DEPENDENCY)

    def add_dependency(self, name: str, dependency: "Resource") -> None:
        """
        Record a named dependency relationship.

        Args:
            name: Name of dependency in parent resource
            dependency: The dependent resource
        """
        self.dependencies[name] = dependency

    def get_dependency(self, name: str) -> "Resource | None":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to look up

        Returns:
            Dependency resource or None if not found
        """
        return cast("Resource", self.dependencies.get(name))

    def remove_dependency(self, name: str) -> "Resource | None":
        """
        Remove and return named dependency if it exists.

        Args:
            name: Name of dependency to remove

        Returns:
            Removed resource or None if not found
        """
        return cast("Resource", self.dependencies.pop(name, None))

    def detach_dependent(self, resource: str) -> None:
        """
        Detach a reference to this resource.

        Args:
            resource: Resource key or root variable to detach
        """
        self.detached_dependents.add(resource)

    def __repr__(self) -> str:
        return (
            "<DependencyNode: "
            f"\nresource={self.resource.readable_name}, "
            f"\nresource_key={self.resource.key}, "
            f"\ndependencies_count={len(self.dependencies)}, "
            f"\ndependents_count={len(self.dependents)}, "
            f"\ndetached_dependents={len(self.detached_dependents)}, "
            f"\ncontext={self.context}), "
            "\n>"
        )
