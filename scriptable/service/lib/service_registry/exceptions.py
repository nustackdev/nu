from scriptable.service.exceptions import ServiceError


class RegistryError(ServiceError):
    """Base exception for registry-related errors."""

    pass


class RegistryStateError(RegistryError):
    """Raised when registry is in invalid state."""

    pass


class RegistryKeyError(RegistryError):
    """Raised when service key is invalid or not found."""

    pass
