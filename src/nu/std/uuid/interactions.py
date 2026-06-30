"""UUID constructor interactions - one ``ScalarQueryFactory`` binding each.

Core can't build a ``uuid.UUID``, so the constructors are the only atoms this
module adds. Everything else a UUID does (attribute reads, comparison) reuses
core interactions, so it lives on the Form, not here.

``Uuid4Query`` / ``Uuid1Query`` are non-deterministic (they read randomness /
the clock), so a future constant-folding pass must treat them as impure
(open item until the model grows a purity tag).
"""

from __future__ import annotations

from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.lang import ScalarQueryFactory


__all__ = [
    "Uuid1Query",
    "Uuid3Query",
    "Uuid4Query",
    "Uuid5Query",
    "UuidFromBytesQuery",
    "UuidFromIntQuery",
    "UuidFromStrQuery",
]


Uuid4Query = ScalarQueryFactory("Uuid4Query", uuid4)
Uuid1Query = ScalarQueryFactory("Uuid1Query", uuid1)
Uuid3Query = ScalarQueryFactory("Uuid3Query", uuid3)
Uuid5Query = ScalarQueryFactory("Uuid5Query", uuid5)
UuidFromStrQuery = ScalarQueryFactory("UuidFromStrQuery", lambda v: UUID(str(v)))
UuidFromBytesQuery = ScalarQueryFactory("UuidFromBytesQuery", lambda b: UUID(bytes=b))
UuidFromIntQuery = ScalarQueryFactory("UuidFromIntQuery", lambda i: UUID(int=int(i)))
