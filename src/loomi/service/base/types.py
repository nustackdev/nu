"""
Type definitions for the service system.

This module provides type aliases and custom types used throughout the
service implementation. It centralizes type definitions to avoid circular
imports while providing type checking support.
"""

from __future__ import annotations

from typing import NewType

__all__ = [
    "ServiceKey",
]

ServiceKey = NewType("ServiceKey", str)
"""Type for unique service instance identifiers."""
