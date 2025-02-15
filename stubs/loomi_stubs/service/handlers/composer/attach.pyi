from typing import Any, TypeVar

from _typeshed import Incomplete

from loomi.service.base import Service, Spec
from loomi.utils.descriptor import BaseDescriptor

__all__ = ["Attach", "AttachDescriptor", "is_attach_descriptor"]

S = TypeVar("S", bound=Service)
T = TypeVar("T")

class AttachDescriptor(BaseDescriptor[S]):
    default_factory: Incomplete
    spec: Incomplete
    spec_key: Incomplete
    allow_override: Incomplete
    def __init__(
        self,
        default_factory: type[S] | None = None,
        /,
        *,
        spec: Spec | None = None,
        spec_key: str | None = None,
        allow_override: bool = True,
    ) -> None: ...

def Attach(type: type[T], spec: Spec | None = None) -> T: ...
def is_attach_descriptor(obj: Any) -> bool: ...
