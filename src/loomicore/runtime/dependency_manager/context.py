from __future__ import annotations

from dataclasses import dataclass, field

from .types import ResourceRole

__all__ = [
    "ResourceContext",
]


@dataclass
class ResourceContext:
    """
    Tracks resource creation context and roles throughout its lifecycle.

    This class maintains both historical information about how a resource
    was originally created and its current usage within the system. This
    dual tracking enables proper cleanup decisions that consider both
    the resource's origin and its current relationships.

    Attributes:
        original_role: The role resource was first created with (immutable)
        active_roles: Current roles resource holds (can change over time)
        root_usage_count: Number of times used as root resource
        dependency_usage_count: Number of times used as dependency
    """

    # Immutable creation context
    original_role: ResourceRole

    # Current active roles (can be both ROOT and DEPENDENCY)
    active_roles: set[ResourceRole] = field(default_factory=set)

    # Track different types of usage
    root_usage_count: int = 0
    dependency_usage_count: int = 0

    @property
    def is_active(self) -> bool:
        """
        Check if resource is still actively used in any role.

        Returns:
            True if resource has any active usage
        """
        return self.root_usage_count > 0 or self.dependency_usage_count > 0

    def add_role(self, role: ResourceRole) -> None:
        """
        Add a new role and update corresponding usage counts.

        A resource can hold both ROOT and DEPENDENCY roles simultaneously
        when it's being used both directly and as a dependency.

        Args:
            role: Role to add to this resource
        """
        self.active_roles.add(role)
        if role == ResourceRole.ROOT:
            self.root_usage_count += 1
        else:
            self.dependency_usage_count += 1

    def remove_role(self, role: ResourceRole) -> None:
        """
        Remove a role and update usage counts.

        When counts reach zero, the role is removed from active_roles.
        Counts are prevented from going negative.

        Args:
            role: Role to remove
        """
        if role == ResourceRole.ROOT:
            self.root_usage_count = max(0, self.root_usage_count - 1)
            if self.root_usage_count == 0:
                self.active_roles.discard(role)
        else:
            self.dependency_usage_count = max(0, self.dependency_usage_count - 1)
            if self.dependency_usage_count == 0:
                self.active_roles.discard(role)

    def __repr__(self) -> str:
        roles = ", ".join(
            f"{role.name}({self.root_usage_count if role == ResourceRole.ROOT else self.dependency_usage_count})"
            for role in self.active_roles
        )
        return f"<ResourceContext: {roles}>"
