"""HTTP MethodRefs: one Ref class per verb, declaration-style.

Each verb Ref inlines `.method(...)` and `__call__` directly. Repetition
is intentional: this is a declarative surface, and inlining keeps every
verb readable end-to-end without hopping to a base class.

`.method(...)` is annotated as returning the Ref subclass itself
(`-> POSTRef`, `-> GETRef`, ...). That is a deliberate lie: at runtime it
returns a `Method` declaration which the ServiceMeta descriptor unwraps at
class access. The lie makes `Solana.get_slot` resolve to `POSTRef` in a
type checker, so `Solana.get_slot(...)` type-checks as `POSTRef.__call__`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import HttpDelete, HttpGet, HttpPatch, HttpPost, HttpPut


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["DELETERef", "GETRef", "PATCHRef", "POSTRef", "PUTRef"]


class GETRef(MethodRef):
    """GET endpoint Ref."""

    @classmethod
    def method(cls, path: str, **defaults: object) -> GETRef:  # type: ignore[override]
        """Declare a GET endpoint at `path`. Actually returns a Method (typing lie for descriptor access)."""
        return Method(cls, verb="GET", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct HttpGet over the given kwargs."""
        return HttpGet(self, Dict.of(**kwargs))


class POSTRef(MethodRef):
    """POST endpoint Ref."""

    @classmethod
    def method(cls, path: str, **defaults: object) -> POSTRef:  # type: ignore[override]
        """Declare a POST endpoint at `path`. Actually returns a Method (typing lie for descriptor access)."""
        return Method(cls, verb="POST", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct HttpPost over the given kwargs."""
        return HttpPost(self, Dict.of(**kwargs))


class PUTRef(MethodRef):
    """PUT endpoint Ref."""

    @classmethod
    def method(cls, path: str, **defaults: object) -> PUTRef:  # type: ignore[override]
        """Declare a PUT endpoint at `path`. Actually returns a Method (typing lie for descriptor access)."""
        return Method(cls, verb="PUT", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct HttpPut over the given kwargs."""
        return HttpPut(self, Dict.of(**kwargs))


class PATCHRef(MethodRef):
    """PATCH endpoint Ref."""

    @classmethod
    def method(cls, path: str, **defaults: object) -> PATCHRef:  # type: ignore[override]
        """Declare a PATCH endpoint at `path`. Actually returns a Method (typing lie for descriptor access)."""
        return Method(cls, verb="PATCH", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct HttpPatch over the given kwargs."""
        return HttpPatch(self, Dict.of(**kwargs))


class DELETERef(MethodRef):
    """DELETE endpoint Ref."""

    @classmethod
    def method(cls, path: str, **defaults: object) -> DELETERef:  # type: ignore[override]
        """Declare a DELETE endpoint at `path`. Actually returns a Method (typing lie for descriptor access)."""
        return Method(cls, verb="DELETE", path=path, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Construct HttpDelete over the given kwargs."""
        return HttpDelete(self, Dict.of(**kwargs))
