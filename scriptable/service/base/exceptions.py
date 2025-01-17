from __future__ import annotations


class ServiceError(Exception):
    """Base exception for all service-related errors."""

    pass


class CreationError(Exception):
    """Raised when service creation fails."""

    pass


class StateError(ServiceError):
    """Raised when service is in invalid state for operation."""

    pass


class SpecError(ServiceError):
    """Raised when service there is an error with service spec."""

    pass
