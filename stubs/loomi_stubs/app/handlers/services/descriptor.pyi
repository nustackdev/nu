from typing import TypeVar

from _typeshed import Incomplete

from loomi.service import Service, Spec
from loomi.utils.descriptor import BaseDescriptor

__all__ = ["ServiceDescriptor", "UseService"]

S = TypeVar("S", bound=Service)

class ServiceDescriptor(BaseDescriptor[S]):
    default_factory: Incomplete
    spec: Incomplete
    spec_key: Incomplete
    as_state: Incomplete
    def __init__(
        self,
        default_factory: type[S] | None = None,
        /,
        *,
        spec: Spec | None = None,
        spec_key: str | None = None,
        as_state: bool = False,
    ) -> None: ...

def UseService(type: type[S], spec: Spec | None = None) -> S: ...
