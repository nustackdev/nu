from typing import TypeVar

from loomi.service import Service, Spec

__all__ = ["UseState"]

S = TypeVar("S", bound=Service)

def UseState(type: type[S], spec: Spec | None = None) -> S: ...
