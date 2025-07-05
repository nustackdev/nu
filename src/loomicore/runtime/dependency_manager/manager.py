"""
Resource dependency management system.

This module implements a dependency management system that handles
resource lifecycle, relationships, and cleanup. The system is designed to properly
handle resources that can transition between being root resources and dependencies
while maintaining proper lifecycle tracking.

Key Features:
- Context-aware resource lifecycle management
- Role transition support (root <-> dependency)
- Smart cleanup based on both creation context and current relationships
- Thread-safe composite operations (to implement)
- Circular dependency detection
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, cast

from .exceptions import CircularDependencyError, DependencyError, DependencyNotFoundError
from .logger import logger
from .node import DependencyNode

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.spec import Spec

    from ..resource_registry import ResourceRegistry

__all__ = [
    "DependencyManager",
]


class DependencyManager:
    """
    Manages resource dependency relationships and lifecycle decisions.

    This class is the core of the dependency management system. It handles:
    - Resource registration and role tracking
    - Dependency resolution and relationship management
    - Cleanup decision making based on context and relationships
    - Thread-safe operations for concurrent access

    The manager uses a graph structure where resources are nodes and
    dependencies are edges. Each node tracks both its relationships and
    usage context to enable smart cleanup decisions.

    Key Features:
    - Context-aware resource management
    - Role transition support
    - Smart cleanup based on both history and current state
    - Thread-safe operations
    - Circular dependency detection
    """

    def __init__(self, registry: "ResourceRegistry") -> None:
        """
        Initialize dependency manager.

        Args:
            registry: Resource registry to coordinate with
        """
        self._registry = registry
        self._nodes: dict[str, DependencyNode] = {}
        self._lock = Lock()
        logger.debug("Initialized dependency manager")

    def register_resource(self, resource: "Resource", is_dependency: bool = False) -> None:
        """
        Register resource with proper context tracking.

        If resource already exists, updates its context for the new role.
        New resources get a fresh context based on their creation role.

        Args:
            resource: Resource to register
            is_dependency: Whether registering as dependency
        """
        if not self._node_exists(resource):
            self._create_node(resource, is_dependency)

        # If not a dependency, register as new root
        if not is_dependency:
            self._get_node(resource).register_root()

    def resolve_dependency(
        self,
        parent: "Resource",
        name: str,
        spec: Spec,
    ) -> "Resource":
        """
        Resolve dependency relationship, creating resource if needed.

        This method handles the complete dependency resolution process:
        1. Creates/gets dependency resource instance
        2. Validates no cycles would be created
        3. Establishes relationship tracking

        Args:
            parent: Resource requesting dependency
            name: Dependency name in parent
            spec: Dependency specification

        Returns:
            Resolved dependency resource

        Raises:
            DependencyError: Invalid spec or circular dependency
        """
        if not self._node_exists(parent):
            raise DependencyError(
                f"Parent resource not found: '{parent.readable_name}'. Register first."
            )

        factory = spec.factory
        if factory is None:
            raise DependencyError(f"Missing factory for dependency '{name}'")

        # Create with dependency context
        dependency = factory(spec, __is_dependency__=True)  # type: ignore
        if not dependency:
            raise DependencyNotFoundError(
                f"Failed to resolve dependency '{name}' for '{parent.readable_name}'"
            )

        self._validate_no_cycles(parent, dependency)

        self.add_relationship(parent, name, dependency)

        return dependency

    def add_relationship(
        self,
        parent: "Resource",
        name: str,
        child: "Resource",
    ) -> None:
        """
        Record new dependency relationship.

        Establishes bidirectional relationship tracking and updates
        contexts for both resources appropriately.

        Args:
            parent: Parent resource
            name: Dependency name in parent
            child: Child (dependency) resource
        """
        parent_node = self._get_node(parent)
        child_node = self._get_node(child)

        parent_node.add_dependency(name, child)
        child_node.add_dependent(parent)

        logger.debug(
            f"Added relationship: '{parent.readable_name}.{name}' -> '{child.readable_name}'"
        )

    def get_dependencies(self, resource: "Resource") -> dict[str, "Resource"]:
        """
        Get all dependencies of a resource.

        Args:
            resource: Resource to get dependencies for

        Returns:
            Dict mapping dependency names to resources

        Raises:
            DependencyError: If resource not found
        """
        return dict(self._get_node(resource).dependencies)

    def get_dependents(self, resource: "Resource") -> set["Resource"]:
        """
        Get all resources depending on given resource.

        Args:
            resource: Resource to get dependents for

        Returns:
            Set of dependent resources

        Raises:
            DependencyError: If resource not found
        """
        return set(self._get_node(resource).dependents)

    def detach_relationship(self, parent: "Resource", child: "Resource") -> None:
        """
        Register a dateched parent (dependent) resource.

        Args:
            parent: Parent (dependent) resource
            child: Child  resource
        """
        child_node = self._get_node(child)
        child_node.detach_dependent(parent.key)

    def can_auto_shutdown(self, resource: "Resource") -> bool:
        """
        Determine if resource can be auto shut down (cascade shutdown triggered from dependent).

        A resource can be auto shut down if all these conditions are met:
        1. Has no registered direct (root) usage
        2. All dependents are detached

        Args:
            resource: Resource to check

        Returns:
            True if resource can be shutdown
        """
        node = self._get_node(resource)

        # Check if no direct usage
        if node.context.root_usage_count > 0:
            return False

        # Check if all dependents are detached
        dependents = node.dependents
        detached_dependents = node.detached_dependents

        if {dep.key for dep in dependents} != detached_dependents:
            return False

        return True

    def _validate_no_cycles(self, parent: "Resource", child: "Resource") -> None:
        """
        Ensure no dependency cycles would be created.

        Raises:
            CircularDependencyError: If cycle would be created
        """
        visited: set[str] = {parent.key}
        self._check_cycles(child, visited)

    def _check_cycles(self, current: "Resource", visited: set[str]) -> None:
        """Recursively check for dependency cycles."""
        if current.key in visited:
            path = " -> ".join(self._nodes[key].resource.readable_name for key in visited)
            raise CircularDependencyError(
                f"Circular dependency detected: {path} -> {current.readable_name}"
            )

        visited.add(current.key)
        for dep in self.get_dependencies(current).values():
            self._check_cycles(cast("Resource", dep), visited)
        visited.remove(current.key)

    def _node_exists(self, resource: "Resource") -> bool:
        """
        Check if node exists for resource.

        Args:
            resource: Resource to check

        Returns:
            True if node exists
        """
        return resource.key in self._nodes

    def _get_node(self, resource: "Resource") -> DependencyNode:
        """
        Get existing node.

        Args:
            resource: Resource needing a node

        Returns:
            Resource node

        Raises:
            DependencyError: If node not found
        """
        node = self._nodes.get(resource.key, None)
        if node is None:
            raise DependencyError(f"Node not found for {resource.readable_name}")
        return node

    def _create_node(self, resource: "Resource", is_dependency: bool = False) -> None:
        """
        Create a new resource node with proper context.

        Args:
            resource: Resource needing a node
            is_dependency: Whether creating for dependency

        Raises:
            DependencyError: If node already exists
        """
        node = self._nodes.get(resource.key, None)
        if not node:
            node = DependencyNode(resource, is_dependency)
            self._nodes[resource.key] = node
        else:
            raise DependencyError(f"Node already exists for {resource.readable_name}")

    def __repr__(self) -> str:
        """
        Return a string representation of the dependency graph.

        Includes:
        - Total number of nodes
        - String representation of dependency chains
        - Repr of each dependency node
        """
        node_count = len(self._nodes)

        # Generate node reprs
        nodes_repr = "\n * ".join(repr(node) for node in self._nodes.values())

        # Generate chain reprs
        chains = []
        for node in self._nodes.values():
            resource_name = node.resource.readable_name
            dependencies = ", ".join(dep.readable_name for dep in node.dependencies.values())
            chains.append(f"{resource_name} -> [{dependencies}]")
        chains = "\n * ".join(chains)

        return (
            "<DependencyManager:"
            f"\n\nNodes ({node_count}):"
            f"\n * {nodes_repr}"
            f"\n\nChains:"
            f"\n * {chains}"
            "\n>"
        )
