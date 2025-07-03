"""
Exception hierarchy for resource pool operations.

This module defines the complete exception hierarchy for resource pools,
providing specific error types for different components and failure scenarios.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "ResourcePoolError",
    "WorkerError",
    "AdapterError",
    "BalancerError",
    "ProtocolError",
    "WorkerStartupError",
    "WorkerShutdownError",
    "WorkerHealthError",
    "AdapterConfigurationError",
    "AdapterConnectionError",
    "BalancerConfigurationError",
    "BalancerSelectionError",
    "ProtocolConfigurationError",
    "ProtocolConnectionError",
]


class ResourcePoolError(Exception):
    """
    Base exception for all resource pool related errors.

    This is the root exception that all other resource pool exceptions
    inherit from. It provides common functionality for error context
    and debugging information.
    """

    def __init__(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize resource pool error.

        Args:
            message: Human-readable error message
            context: Additional context information for debugging
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        """Enhanced string representation with context."""
        msg = super().__str__()

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg = f"{msg} (context: {context_str})"

        if self.cause:
            msg = f"{msg} (caused by: {type(self.cause).__name__}: {self.cause})"

        return msg


# --- Worker-related exceptions ---


class WorkerError(ResourcePoolError):
    """Base exception for worker-related errors."""

    def __init__(
        self,
        message: str,
        *,
        worker_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize worker error.

        Args:
            message: Error message
            worker_id: ID of the worker that caused the error
            endpoint: Endpoint address of the worker
            **kwargs: Additional context passed to parent
        """
        context = kwargs.get("context", {})
        if worker_id:
            context["worker_id"] = worker_id
        if endpoint:
            context["endpoint"] = endpoint
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class WorkerStartupError(WorkerError):
    """Raised when a worker fails to start properly."""

    def __init__(self, message: str, *, failed_workers: Optional[List[str]] = None, **kwargs):
        """
        Initialize worker startup error.

        Args:
            message: Error message
            failed_workers: List of worker IDs that failed to start
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if failed_workers:
            context["failed_workers"] = failed_workers
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class WorkerShutdownError(WorkerError):
    """Raised when a worker fails to shutdown properly."""

    def __init__(self, message: str, *, timeout_workers: Optional[List[str]] = None, **kwargs):
        """
        Initialize worker shutdown error.

        Args:
            message: Error message
            timeout_workers: List of worker IDs that failed to shutdown gracefully
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if timeout_workers:
            context["timeout_workers"] = timeout_workers
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class WorkerHealthError(WorkerError):
    """Raised when worker health checks fail."""

    def __init__(
        self,
        message: str,
        *,
        unhealthy_workers: Optional[List[str]] = None,
        health_check_failures: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize worker health error.

        Args:
            message: Error message
            unhealthy_workers: List of unhealthy worker IDs
            health_check_failures: Number of consecutive health check failures
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if unhealthy_workers:
            context["unhealthy_workers"] = unhealthy_workers
        if health_check_failures is not None:
            context["health_check_failures"] = health_check_failures
        kwargs["context"] = context

        super().__init__(message, **kwargs)


# --- Adapter-related exceptions ---


class AdapterError(ResourcePoolError):
    """Base exception for adapter-related errors."""

    def __init__(self, message: str, *, adapter_type: Optional[str] = None, **kwargs):
        """
        Initialize adapter error.

        Args:
            message: Error message
            adapter_type: Type of adapter that caused the error
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if adapter_type:
            context["adapter_type"] = adapter_type
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class AdapterConfigurationError(AdapterError):
    """Raised when adapter configuration is invalid."""

    def __init__(self, message: str, *, invalid_config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize adapter configuration error.

        Args:
            message: Error message
            invalid_config: Invalid configuration that caused the error
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if invalid_config:
            context["invalid_config"] = invalid_config
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class AdapterConnectionError(AdapterError):
    """Raised when adapter fails to connect to worker backend."""

    pass


# --- Balancer-related exceptions ---


class BalancerError(ResourcePoolError):
    """Base exception for load balancer related errors."""

    def __init__(self, message: str, *, balancer_type: Optional[str] = None, **kwargs):
        """
        Initialize balancer error.

        Args:
            message: Error message
            balancer_type: Type of balancer that caused the error
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if balancer_type:
            context["balancer_type"] = balancer_type
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class BalancerConfigurationError(BalancerError):
    """Raised when balancer configuration is invalid."""

    def __init__(self, message: str, *, worker_count: Optional[int] = None, **kwargs):
        """
        Initialize balancer configuration error.

        Args:
            message: Error message
            worker_count: Number of workers configured
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if worker_count is not None:
            context["worker_count"] = worker_count
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class BalancerSelectionError(BalancerError):
    """Raised when balancer cannot select a healthy worker."""

    def __init__(
        self,
        message: str,
        *,
        available_workers: Optional[int] = None,
        total_workers: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize balancer selection error.

        Args:
            message: Error message
            available_workers: Number of available workers
            total_workers: Total number of workers
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if available_workers is not None:
            context["available_workers"] = available_workers
        if total_workers is not None:
            context["total_workers"] = total_workers
        kwargs["context"] = context

        super().__init__(message, **kwargs)


# --- Protocol-related exceptions ---


class ProtocolError(ResourcePoolError):
    """Base exception for protocol-related errors."""

    def __init__(
        self,
        message: str,
        *,
        protocol: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize protocol error.

        Args:
            message: Error message
            protocol: Protocol type that caused the error
            endpoint: Endpoint address involved in the error
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if protocol:
            context["protocol"] = protocol
        if endpoint:
            context["endpoint"] = endpoint
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class ProtocolConfigurationError(ProtocolError):
    """Raised when protocol configuration is invalid."""

    def __init__(self, message: str, *, invalid_params: Optional[List[str]] = None, **kwargs):
        """
        Initialize protocol configuration error.

        Args:
            message: Error message
            invalid_params: List of invalid configuration parameters
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if invalid_params:
            context["invalid_params"] = invalid_params
        kwargs["context"] = context

        super().__init__(message, **kwargs)


class ProtocolConnectionError(ProtocolError):
    """Raised when protocol fails to establish connection."""

    def __init__(
        self,
        message: str,
        *,
        connection_timeout: Optional[float] = None,
        retry_count: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize protocol connection error.

        Args:
            message: Error message
            connection_timeout: Timeout value used for connection
            retry_count: Number of connection retries attempted
            **kwargs: Additional context
        """
        context = kwargs.get("context", {})
        if connection_timeout is not None:
            context["connection_timeout"] = connection_timeout
        if retry_count is not None:
            context["retry_count"] = retry_count
        kwargs["context"] = context

        super().__init__(message, **kwargs)


# Convenience functions for common error scenarios


def worker_startup_failed(worker_ids: List[str], cause: Exception) -> WorkerStartupError:
    """Create WorkerStartupError for failed worker startup."""
    return WorkerStartupError(
        f"Failed to start {len(worker_ids)} workers: {worker_ids}",
        failed_workers=worker_ids,
        cause=cause,
    )


def no_healthy_workers() -> BalancerSelectionError:
    """Create BalancerSelectionError for no healthy workers."""
    return BalancerSelectionError(
        "No healthy workers available for load balancing", available_workers=0
    )


def unsupported_protocol(protocol: str) -> ProtocolConfigurationError:
    """Create ProtocolConfigurationError for unsupported protocol."""
    return ProtocolConfigurationError(
        f"Unsupported protocol: {protocol}", protocol=protocol, invalid_params=["protocol"]
    )


def adapter_not_configured(adapter_type: str) -> AdapterConfigurationError:
    """Create AdapterConfigurationError for missing adapter configuration."""
    return AdapterConfigurationError(
        f"Adapter not properly configured: {adapter_type}", adapter_type=adapter_type
    )
