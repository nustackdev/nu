"""UUID constructor interactions - one ``host`` binding each.

Core can't build a ``uuid.UUID``, so the constructors are the only atoms this
module adds. Everything else a UUID does (attribute reads, comparison) reuses
core interactions, so it lives on the Form, not here.

``Uuid4Query`` / ``Uuid1Query`` read randomness / the clock. ``uuid3`` /
``uuid5`` are pure functions of their args.
"""

from __future__ import annotations

from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from nu.factory import host


__all__ = [
    "Uuid1Query",
    "Uuid3Query",
    "Uuid4Query",
    "Uuid5Query",
    "UuidFromBytesQuery",
    "UuidFromIntQuery",
    "UuidFromStrQuery",
]


Uuid4Query = host(uuid4, name="Uuid4Query")
Uuid1Query = host(uuid1, name="Uuid1Query")
Uuid3Query = host(uuid3, name="Uuid3Query")
Uuid5Query = host(uuid5, name="Uuid5Query")
UuidFromStrQuery = host(lambda v: UUID(str(v)), name="UuidFromStrQuery")
UuidFromBytesQuery = host(lambda b: UUID(bytes=b), name="UuidFromBytesQuery")
UuidFromIntQuery = host(lambda i: UUID(int=int(i)), name="UuidFromIntQuery")
