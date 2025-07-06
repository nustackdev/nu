"""
ResourceMeta metaclass - pure delegation to runtime system.

This module provides the ResourceMeta metaclass that handles resource
instantiation by delegating all creation logic to the runtime system.
This maintains the clean separation between the user interface (Resource classes)
and the implementation (Runtime system).

The metaclass intercepts resource creation and delegates to the runtime's
ResourceFactory, which handles:
- Resource deduplication based on specifications
- Dependency resolution and composition
- Lifecycle state management
- Thread-safe creation and registration

Design Philosophy:
    - Ultra-thin delegation layer
    - No operational logic in metaclass
    - All complexity handled by runtime
    - Clean separation of concerns
"""

from __future__ import annotations

from typing import Any

from loomicore.runtime import get_resource_runtime
from loomicore.spec import Spec

__all__ = [
    "ResourceMeta",
]


class ResourceMeta(type):
    """
    Metaclass for resource classes providing pure delegation to runtime.

    This metaclass intercepts resource class instantiation and delegates
    all creation logic to the runtime system. It maintains the clean
    separation between user interface and implementation by ensuring
    resources are created through the proper runtime channels.

    The metaclass handles:
    - Intercepting __call__ during resource instantiation
    - Delegating to runtime ResourceFactory for actual creation
    - Maintaining factory name identification for runtime

    All operational logic (deduplication, dependency resolution, state
    management) is handled by the runtime system, keeping this metaclass
    minimal and focused.
    """

    def __call__(cls, spec: Spec | None = None, /, *args: Any, **kwargs: Any) -> Any:
        """
        Intercept resource instantiation and delegate to runtime factory.

        This method is called whenever a resource class is instantiated
        (e.g., MyResource(spec)). Instead of creating the instance directly,
        it delegates to the runtime system which handles all the complexity
        of resource creation, deduplication, and lifecycle management.

        Args:
            spec: Resource specification defining instance properties.
                 If None, runtime will create default spec.
            *args: Additional positional arguments passed to runtime
            **kwargs: Additional keyword arguments passed to runtime

        Returns:
            Resource instance created and managed by runtime system

        Notes:
            - Import at call-time prevents circular import issues
            - All arguments passed through to runtime factory
            - Runtime handles deduplication, dependency resolution, etc.
            - Resource may be existing instance if spec matches existing resource
        """
        return get_resource_runtime().resource_factory.create_resource(cls, spec, *args, **kwargs)  # type: ignore
