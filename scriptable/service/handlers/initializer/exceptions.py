from scriptable.service.exceptions import ServiceError


class InitializationError(ServiceError):
    """Raised when service initialization fails."""

    pass


class ShutdownError(ServiceError):
    """Raised when service shutdown fails."""

    pass
