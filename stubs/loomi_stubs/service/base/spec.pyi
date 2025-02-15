from pydantic import BaseModel

from .bases import Service
from .types import ServiceKey

__all__ = ["Spec"]

class Spec(BaseModel):
    class Config:
        arbitrary_types_allowed: bool
        extra: str
        from_attributes: bool
        frozen: bool

    name: str
    factory: type | None
    @classmethod
    def identity_fields(cls) -> set[str] | None: ...
    @classmethod
    def default_identity_fields(cls) -> set[str] | None: ...
    def serialize_factory(self, factory: type[Service]) -> str: ...
    def identity(self) -> dict: ...
    @property
    def key(self) -> ServiceKey: ...
