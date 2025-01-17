from typing import Any, Type


class ValidationError(Exception):
    """Base class for validation errors."""

    def __init__(self, message: str, field_name: str, value: Any, expected_type: Type) -> None:
        self.field_name = field_name
        self.value = value
        self.expected_type = expected_type
        super().__init__(f"{message} (field: {field_name}, got: {value})")


class TypeValidationError(ValidationError):
    """Raised when type validation fails."""

    pass


class ValueValidationError(ValidationError):
    """Raised when custom validation fails."""

    pass
