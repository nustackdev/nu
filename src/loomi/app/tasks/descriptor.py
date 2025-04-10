"""
Descriptor implementation for state configuration.

This module provides descriptor implementation that enable configuring app state.
"""

from __future__ import annotations

from typing import TypeVar

from loomi.app.services import ServiceDescriptor
from loomi.service import Service, Spec

__all__ = [
    "UseEngine",
]

S = TypeVar("S", bound=Service)


def UseEngine(type: type[S], spec: Spec | None = None) -> S:
    """Create a service specification."""
    return ServiceDescriptor[S](spec=spec, as_state=False, as_engine=True)  # type: ignore
