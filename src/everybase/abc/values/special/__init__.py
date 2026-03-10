"""Special value types."""

from .any_ import AnyValue
from .none_ import NoneValue
from .sentinel_ import EmptyValue, InvalidValue, SentinelValue


__all__ = ["AnyValue", "EmptyValue", "InvalidValue", "NoneValue", "SentinelValue"]
