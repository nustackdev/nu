class AppError(Exception):
    """Base class all app-related exceptions."""

    pass


class HandlerNotImplemented(AppError):
    """Handler not implemented for app."""

    pass
