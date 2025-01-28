"""
Type definitions for the service system.

This module provides type aliases and custom types used throughout the
service implementation. It centralizes type definitions to avoid circular
imports while providing type checking support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NewType, TypeAlias

if TYPE_CHECKING:
    from .bases import ServiceAsyncBase, ServiceBase, ServiceSyncBase

# Core type definitions
ServiceKey = NewType("ServiceKey", str)
"""Type for unique service instance identifiers."""

ServiceType: TypeAlias = "ServiceSyncBase | ServiceAsyncBase | ServiceBase"
"""
Type alias representing any service instance type.
ServiceSyncBase, ServiceAsyncBase, and ServiceCommonBase are all valid service types.
- ServiceSyncBase: Synchronous service instance
- ServiceAsyncBase: Asynchronous service instance
- ServiceBase: Base service instance
"""


__all__ = ["ServiceKey", "ServiceType"]
