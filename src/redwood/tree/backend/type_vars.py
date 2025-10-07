from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar


if TYPE_CHECKING:
    from .types import Value

__all__ = [
    "ValueT",
    "ValueT_co",
    "ValueT_contra",
]


ValueT = TypeVar("ValueT", bound="Value")
ValueT_co = TypeVar("ValueT_co", bound="Value", covariant=True)
ValueT_contra = TypeVar("ValueT_contra", bound="Value", contravariant=True)
