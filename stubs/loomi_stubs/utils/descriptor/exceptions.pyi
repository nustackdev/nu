from typing import Any

from _typeshed import Incomplete

__all__ = ["ValidationError", "TypeValidationError", "ValueValidationError"]

class ValidationError(Exception):
    field_name: Incomplete
    value: Incomplete
    expected_type: Incomplete
    def __init__(self, message: str, field_name: str, value: Any, expected_type: type) -> None: ...

class TypeValidationError(ValidationError): ...
class ValueValidationError(ValidationError): ...
