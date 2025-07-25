"""
Generic Spec Builder - Clean implementation without complex generics

Provides a completely generic builder that works with any spec type,
using simple type hints instead of complex generic annotations.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Tuple

import attrs

from loomicore.spec import ProxySpec, ResourceSpec, Spec

__all__ = [
    "SpecBuilder",
    "ProxySpec",
    "ResourceSpec",
    "Spec",
    "AppSpec",
]


@attrs.define(frozen=True, slots=True, kw_only=True)
class AppSpec(ResourceSpec):
    """
    Specification for an application.

    This is a placeholder for application-specific configurations.
    """

    state: Optional[Spec] = None
    evaluator: Optional[Spec] = None


class SpecBuilder:
    """
    Generic spec builder that works with any spec type.

    Provides only generic transformations:
    - as_proxy(): Wrap any spec in ProxySpec with provided client spec
    - with_launcher(): Add launcher spec to ProxySpec
    - replicate(): Create multiple instances with explicit path substitution
    - with_value(): Delegate to existing Spec.with_value()

    Examples:
        # Basic transformations
        client_spec = RPyCUnixClientSpec(connection=RPyCUnixConnectionSpec(socket_path="/tmp/state.sock"))
        launcher_spec = MultiprocessingLauncherSpec(host=RPyCUnixServerSpec(socket_path="/tmp/state.sock"))

        SpecBuilder(state_spec)
            .as_proxy(client_spec)
            .with_launcher(launcher_spec)
            .build()

        # Replication with explicit paths
        SpecBuilder(worker_spec)
            .as_proxy(client_spec)
            .with_launcher(launcher_spec)
            .replicate(4, paths={
                ("client_spec", "connection", "socket_path"): "/tmp/worker_{}.sock",
                ("launcher_spec", "host", "socket_path"): "/tmp/worker_{}.sock",
                ("inner_spec", "name"): "worker_{}",
            })
    """

    def __init__(self, spec: Spec):
        self._spec = spec

    def as_proxy(self, client_spec: Spec) -> "SpecBuilder":
        """
        Wrap any spec in ProxySpec with provided client spec.

        Args:
            client_spec: Client specification for proxy communication

        Returns:
            SpecBuilder wrapping ProxySpec
        """
        proxy_spec = ProxySpec(
            inner_spec=self._spec,
            client_spec=client_spec,
        )
        return SpecBuilder(proxy_spec)

    def with_launcher(self, launcher_spec: Spec) -> "SpecBuilder":
        """
        Add launcher capability to ProxySpec.

        Only works if the current spec is a ProxySpec.

        Args:
            launcher_spec: Launcher specification to add

        Returns:
            SpecBuilder with launcher added

        Raises:
            ValueError: If called on non-ProxySpec
        """
        if not isinstance(self._spec, ProxySpec):
            raise ValueError("with_launcher() can only be called on ProxySpec")

        # Create new ProxySpec with launcher
        updated_spec = ProxySpec(
            inner_spec=self._spec.inner_spec,
            client_spec=self._spec.client_spec,
            launcher_spec=launcher_spec,
        )

        return SpecBuilder(updated_spec)

    def replicate(
        self,
        count: int,
        *,
        paths: Dict[Tuple[str, ...], str] | None = None,
        customizer: Callable[[Spec, int], Spec] | None = None,
    ) -> tuple[Spec, ...]:
        """
        Create multiple instances of the spec with explicit path substitution.

        Args:
            count: Number of instances to create (1-indexed)
            paths: Explicit path mappings where:
                   - Keys: Tuple of strings representing nested field path
                   - Values: Pattern string with {} placeholder for index
            customizer: Custom function for spec modification (takes spec and 1-based index)

        Returns:
            List of replicated specs with substituted values

        Examples:
            # Explicit path mapping
            .replicate(4, paths={
                ("client_spec", "connection", "socket_path"): "/tmp/worker_{}.sock",
                ("inner_spec", "name"): "worker_{}",
            })

            # Custom replication logic
            .replicate(3, customizer=lambda spec, i: spec.with_value("name", f"instance_{i}"))
        """
        if customizer:
            return tuple(customizer(self._spec, i) for i in range(1, count + 1))

        if paths is None:
            # No replication patterns provided, just return identical copies
            return tuple([self._spec] * count)

        results = []
        for i in range(1, count + 1):
            spec = self._replicate_with_paths(self._spec, i, paths)
            results.append(spec)

        return tuple(results)

    def with_value(self, *args, **kwargs) -> "SpecBuilder":
        """
        Delegate to existing Spec.with_value() method.

        This leverages the existing spec infrastructure for value updates.
        All arguments are passed through to the spec's with_value method.
        """
        updated_spec = self._spec.with_value_at(*args, **kwargs)
        return SpecBuilder(updated_spec)

    def build(self) -> Spec:
        """Return the final spec."""
        return self._spec

    # Private implementation
    def _replicate_with_paths(
        self, spec: Spec, index: int, paths: Dict[Tuple[str, ...], str]
    ) -> Spec:
        """
        Replicate spec using explicit path mappings.

        Args:
            spec: Source spec to replicate
            index: 1-based index for substitution
            paths: Path mappings with patterns

        Returns:
            New spec with substituted values
        """
        current_spec = spec

        for path_tuple, pattern in paths.items():
            # Substitute index into pattern
            value = pattern.format(index)

            # Apply update using nested path
            try:
                current_spec = current_spec.with_value_at(*path_tuple, value=value)
            except Exception:
                # Skip updates that fail (field might not exist or be updatable)
                continue

        return current_spec
