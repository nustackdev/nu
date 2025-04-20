"""
Descriptor implementation for state configuration.

This module provides descriptor implementation that enable configuring app state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from .use_service import ServiceDescriptor

if TYPE_CHECKING:
    from loomi._service import Service
    from loomi._spec import Spec

__all__ = [
    "UseState",
]

S = TypeVar("S", bound="Service")


def UseState(type: type[S], spec: "Spec | None" = None) -> S:
    """Create a service specification."""
    return ServiceDescriptor[S](spec=spec, as_state=True, as_engine=False)  # type: ignore
