"""
Type definitions for launcher implementations.

This module defines common types used across launcher implementations
for consistency and type safety.
"""

from __future__ import annotations

from typing import Any, Dict, TypeAlias

__all__ = [
    "ConnectionInfo",
    "LauncherConfig",
]

# Connection information returned by launchers
ConnectionInfo: TypeAlias = Dict[str, Any]

# Configuration dictionary for launcher-specific settings
LauncherConfig: TypeAlias = Dict[str, Any]
