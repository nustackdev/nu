class ServiceError(Exception):
    """Base exception for all service-related errors."""

    pass


class HandlerNotImplemented(ServiceError):
    """Handler not implemented for service."""

    pass
