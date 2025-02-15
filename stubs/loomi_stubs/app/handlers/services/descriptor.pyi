from typing import TypeVar

from _typeshed import Incomplete

from loomi.service import Service, Spec
from loomi.utils.descriptor import BaseDescriptor

__all__ = ["ServiceDescriptor", "UseService"]

S = TypeVar("S", bound=Service)
T = TypeVar("T")

class ServiceDescriptor(BaseDescriptor[S]):
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

def UseService(type: type[T], spec: Spec | None = None) -> T: ...
