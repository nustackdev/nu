from scriptable.app.exceptions import AppError


class InitializationError(AppError):
    """Raised when service initialization fails."""

    pass


class ShutdownError(AppError):
    """Raised when service shutdown fails."""

    pass
