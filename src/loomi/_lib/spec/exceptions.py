from __future__ import annotations

__all__ = [
    "SpecError",
]


class SpecError(Exception):
    """
    Exception raised for service specification errors.

    This exception indicates specification-related failures such as:
    - Invalid specification format
    - Missing required specification fields
    - Incompatible specification values
    - Factory configuration errors
    """

    pass
