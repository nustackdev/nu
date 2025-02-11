"""
Service dependency management system.

This module implements a dependency management system that handles
service lifecycle, relationships, and cleanup. The system is designed to properly
handle services that can transition between being root services and dependencies
while maintaining proper lifecycle tracking.

Key Features:
- Context-aware service lifecycle management
- Role transition support (root <-> dependency)
- Smart cleanup based on both creation context and current relationships
- Thread-safe composite operations (to implement)
- Circular dependency detection

Example Usage:
    # Creating a service with dependencies
    service = MyService()  # Root service
    dep = service.get_dependency("cache")  # Dependency

    # Later transitioning
    dep_as_root = CacheService()  # Same service, now as root

    # System properly tracks both usages
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from .exceptions import CircularDependencyError, DependencyError, DependencyNotFoundError
from .logger import logger
from .node import DependencyNode

if TYPE_CHECKING:
    from scriptable.service.base import Service, ServiceKey, Spec
    from scriptable.service.lib.service_registry import ServiceRegistry


class DependencyManager:
    """
    Manages service dependency relationships and lifecycle decisions.

    This class is the core of the dependency management system. It handles:
    - Service registration and role tracking
    - Dependency resolution and relationship management
    - Cleanup decision making based on context and relationships
    - Thread-safe operations for concurrent access

    The manager uses a graph structure where services are nodes and
    dependencies are edges. Each node tracks both its relationships and
    usage context to enable smart cleanup decisions.

    Key Features:
    - Context-aware service management
    - Role transition support
    - Smart cleanup based on both history and current state
    - Thread-safe operations
    - Circular dependency detection

    Example Usage:
        manager = DependencyManager(registry)

        # Register a service
        manager.register_service(service, is_dependency=False)

        # Resolve dependency
        dep = manager.resolve_dependency(service, "cache", spec)

        # Check cleanup
        if manager.should_cleanup(service, initiator.key):
            # Handle cleanup
    """

    def __init__(self, registry: ServiceRegistry) -> None:
        """
        Initialize dependency manager.

        Args:
            registry: Service registry to coordinate with
        """
        self._registry = registry
        self._nodes: dict[ServiceKey, DependencyNode] = {}
        self._lock = Lock()
        logger.debug("Initialized dependency manager")

    def register_service(self, service: "Service", is_dependency: bool = False) -> None:
        """
        Register service with proper context tracking.

        If service already exists, updates its context for the new role.
        New services get a fresh context based on their creation role.

        Args:
            service: Service to register
            is_dependency: Whether registering as dependency
        """
        if not self._node_exists(service):
            self._create_node(service, is_dependency)

        # If not a dependency, register as new root
        if not is_dependency:
            self._get_node(service).register_root()

    def resolve_dependency(
        self,
        parent: "Service",
        name: str,
        spec: Spec,
    ) -> "Service":
        """
        Resolve dependency relationship, creating service if needed.

        This method handles the complete dependency resolution process:
        1. Creates/gets dependency service instance
        2. Validates no cycles would be created
        3. Establishes relationship tracking

        Args:
            parent: Service requesting dependency
            name: Dependency name in parent
            spec: Dependency specification

        Returns:
            Resolved dependency service

        Raises:
            DependencyError: Invalid spec or circular dependency
        """
        if not self._node_exists(parent):
            raise DependencyError(
                f"Parent service not found: '{parent.readable_name}'. Register first."
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
        parent: "Service",
        name: str,
        child: "Service",
    ) -> None:
        """
        Record new dependency relationship.

        Establishes bidirectional relationship tracking and updates
        contexts for both services appropriately.

        Args:
            parent: Parent service
            name: Dependency name in parent
            child: Child (dependency) service
        """
        parent_node = self._get_node(parent)
        child_node = self._get_node(child)

        parent_node.add_dependency(name, child)
        child_node.add_dependent(parent)

        logger.debug(
            f"Added relationship: '{parent.readable_name}.{name}' -> '{child.readable_name}'"
        )

    def get_dependencies(self, service: "Service") -> dict[str, "Service"]:
        """
        Get all dependencies of a service.

        Args:
            service: Service to get dependencies for

        Returns:
            Dict mapping dependency names to services

        Raises:
            DependencyError: If service not found
        """
        return dict(self._get_node(service).dependencies)

    def get_dependents(self, service: "Service") -> set["Service"]:
        """
        Get all services depending on given service.

        Args:
            service: Service to get dependents for

        Returns:
            Set of dependent services

        Raises:
            DependencyError: If service not found
        """
        return set(self._get_node(service).dependents)

    def detach_relationship(self, parent: "Service", child: "Service") -> None:
        """
        Register a dateched parent (dependent) service.

        Args:
            parent: Parent (dependent) service
            child: Child  service
        """
        child_node = self._get_node(child)
        child_node.detach_dependent(parent.key)

    def can_auto_shutdown(self, service: "Service") -> bool:
        """
        Determine if service can be auto shut down (cascade shutdown triggered from dependent).

        A service can be auto shut down if all these conditions are met:
        1. Has no registered direct (root) usage
        2. All dependents are detached

        Args:
            service: Service to check

        Returns:
            True if service can be shutdown
        """
        node = self._get_node(service)

        # Check if no direct usage
        if node.context.root_usage_count > 0:
            return False

        # Check if all dependents are detached
        dependents = node.dependents
        detached_dependents = node.detached_dependents

        if {dep.key for dep in dependents} != detached_dependents:
            return False

        return True

    def _validate_no_cycles(self, parent: "Service", child: "Service") -> None:
        """
        Ensure no dependency cycles would be created.

        Raises:
            CircularDependencyError: If cycle would be created
        """
        visited: set[ServiceKey] = {parent.key}
        self._check_cycles(child, visited)

    def _check_cycles(self, current: "Service", visited: set[ServiceKey]) -> None:
        """Recursively check for dependency cycles."""
        if current.key in visited:
            path = " -> ".join(self._nodes[key].service.readable_name for key in visited)
            raise CircularDependencyError(
                f"Circular dependency detected: {path} -> {current.readable_name}"
            )

        visited.add(current.key)
        for dep in self.get_dependencies(current).values():
            self._check_cycles(dep, visited)
        visited.remove(current.key)

    def _node_exists(self, service: "Service") -> bool:
        """
        Check if node exists for service.

        Args:
            service: Service to check

        Returns:
            True if node exists
        """
        return service.key in self._nodes

    def _get_node(self, service: "Service") -> DependencyNode:
        """
        Get existing node.

        Args:
            service: Service needing a node

        Returns:
            Service node

        Raises:
            DependencyError: If node not found
        """
        node = self._nodes.get(service.key, None)
        if node is None:
            raise DependencyError(f"Node not found for {service.readable_name}")
        return node

    def _create_node(self, service: "Service", is_dependency: bool = False) -> None:
        """
        Create a new service node with proper context.

        Args:
            service: Service needing a node
            is_dependency: Whether creating for dependency

        Raises:
            DependencyError: If node already exists
        """
        node = self._nodes.get(service.key, None)
        if not node:
            node = DependencyNode(service, is_dependency)
            self._nodes[service.key] = node
        else:
            raise DependencyError(f"Node already exists for {service.readable_name}")

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
            service_name = node.service.readable_name
            dependencies = ", ".join(dep.readable_name for dep in node.dependencies.values())
            chains.append(f"{service_name} -> [{dependencies}]")
        chains = "\n * ".join(chains)

        return (
            "<DependencyManager:"
            f"\n\nNodes ({node_count}):"
            f"\n * {nodes_repr}"
            f"\n\nChains:"
            f"\n * {chains}"
            "\n>"
        )
