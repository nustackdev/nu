from __future__ import annotations

from typing import TYPE_CHECKING, NewType, TypeVar

if TYPE_CHECKING:
    from .base import BaseService
    from .spec import Spec

# Core type variables
ServiceT = TypeVar("ServiceT", bound="BaseService")
SpecT = TypeVar("SpecT", bound="Spec")
ServiceKey = NewType("ServiceKey", str)
