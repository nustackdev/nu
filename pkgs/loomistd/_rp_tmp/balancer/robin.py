"""
Round-robin load balancer for resource pools.

This balancer cycles through available workers in round-robin fashion,
ensuring even distribution of load across healthy workers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loomi.service import SyncService
from loomi.spec import Spec, SpecField

from ..logger import logger

__all__ = [
    "RoundRobinBalancer",
    "RoundRobinBalancerSpec",
]


class RoundRobinBalancer(SyncService):
    """
    Round-robin load balancer for resource pools.

    Cycles through available worker client specs in order, providing
    even distribution of requests across healthy workers.
    """

    spec: RoundRobinBalancerSpec

    def setup(self) -> None:
        """Initialize the round-robin balancer."""
        self._client_specs: List[Spec] = []
        self._current_index = 0
        self._total_selections = 0
        self._selection_counts: Dict[str, int] = {}

    def configure(self, client_specs: List[Spec]) -> None:
        """
        Configure the balancer with available worker client specs.

        Args:
            client_specs: List of client specs for connecting to workers
        """
        self._client_specs = client_specs
        self._current_index = 0
        self._selection_counts = {f"worker_{i}": 0 for i in range(len(client_specs))}

        logger.info(f"Round-robin balancer configured with {len(client_specs)} workers")

    def select_remote_spec(self, resource_spec: Spec) -> Optional[Spec]:
        """
        Select a worker and create a remote spec for the given resource.

        Uses round-robin algorithm to select the next available worker,
        then combines the resource spec with the selected worker's client spec.

        Args:
            resource_spec: Specification of the resource to create remotely

        Returns:
            Remote spec configured for selected worker, or None if no workers available
        """
        if not self._client_specs:
            logger.warning("No client specs configured for load balancing")
            return None

        # Get healthy client specs if health checking is enabled
        available_specs = self._get_available_client_specs()

        if not available_specs:
            logger.warning("No healthy workers available")
            return None

        # Select next client spec using round-robin
        selected_client_spec = self._select_next_client_spec(available_specs)

        if selected_client_spec is None:
            return None

        # Create remote spec by combining resource spec with selected client
        try:
            remote_spec = resource_spec.as_remote(selected_client_spec)

            # Update statistics
            self._total_selections += 1
            worker_key = self._get_worker_key(selected_client_spec)
            self._selection_counts[worker_key] = self._selection_counts.get(worker_key, 0) + 1

            logger.debug(f"Selected worker for {resource_spec.factory.__name__}: {worker_key}")

            return remote_spec

        except Exception as e:
            logger.error(f"Failed to create remote spec: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get load balancer statistics.

        Returns:
            Dictionary containing balancer statistics
        """
        return {
            "balancer_type": "round_robin",
            "total_workers": len(self._client_specs),
            "available_workers": len(self._get_available_client_specs()),
            "current_index": self._current_index,
            "total_selections": self._total_selections,
            "selection_counts": dict(self._selection_counts),
            "health_check_enabled": self.spec.health_check_enabled,
        }

    def _get_available_client_specs(self) -> List[Spec]:
        """
        Get list of available (healthy) client specs.

        Returns:
            List of client specs for healthy workers
        """
        if not self.spec.health_check_enabled:
            # If health checking disabled, all specs are available
            return self._client_specs

        # TODO: Implement health checking logic
        # For now, assume all workers are healthy
        # In a full implementation, this would:
        # 1. Test connections to each worker
        # 2. Remove unhealthy workers from the list
        # 3. Cache health status to avoid constant checking

        return self._client_specs

    def _select_next_client_spec(self, available_specs: List[Spec]) -> Optional[Spec]:
        """
        Select the next client spec using round-robin algorithm.

        Args:
            available_specs: List of available client specs

        Returns:
            Selected client spec, or None if no specs available
        """
        if not available_specs:
            return None

        # Simple round-robin selection
        selected_spec = available_specs[self._current_index % len(available_specs)]

        # Advance to next index
        self._current_index = (self._current_index + 1) % len(available_specs)

        return selected_spec

    def _get_worker_key(self, client_spec: Spec) -> str:
        """
        Get a unique key for a worker client spec.

        Args:
            client_spec: Client specification

        Returns:
            Unique key identifying the worker
        """
        # Try to extract worker identifier from spec
        if hasattr(client_spec, "host") and hasattr(client_spec, "port"):
            return f"tcp_{client_spec.host}_{client_spec.port}"
        elif hasattr(client_spec, "socket_path"):
            return f"unix_{client_spec.socket_path}"
        else:
            # Fallback to spec key
            return f"worker_{client_spec.key[:8]}"


class RoundRobinBalancerSpec(Spec):
    """Specification for RoundRobinBalancer."""

    name: str = SpecField(default="round_robin_balancer")
    factory: type = SpecField(default=RoundRobinBalancer)

    # Health checking configuration
    health_check_enabled: bool = SpecField(default=False)
    health_check_interval: float = SpecField(default=30.0)  # Seconds between health checks
    health_check_timeout: float = SpecField(default=5.0)  # Timeout for individual health checks


# Factory function for easy configuration
def create_round_robin_balancer_spec(
    health_check_enabled: bool = False,
    health_check_interval: float = 30.0,
    health_check_timeout: float = 5.0,
) -> RoundRobinBalancerSpec:
    """
    Create a RoundRobinBalancerSpec with common configuration.

    Args:
        health_check_enabled: Whether to perform health checks on workers
        health_check_interval: Seconds between health checks
        health_check_timeout: Timeout for individual health checks

    Returns:
        Configured RoundRobinBalancerSpec
    """
    return RoundRobinBalancerSpec(
        health_check_enabled=health_check_enabled,
        health_check_interval=health_check_interval,
        health_check_timeout=health_check_timeout,
    )
