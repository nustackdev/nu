from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from loomicore.common.descriptor import BaseDescriptor

if TYPE_CHECKING:
    from loomicore.resource import Resource


__all__ = [
    "BaseResourceDescriptor",
]


ResourceType = TypeVar("ResourceType", bound="Resource")


class BaseResourceDescriptor(BaseDescriptor[ResourceType]):
    """Base descriptor for service dependencies with protocol validation."""

    pass
