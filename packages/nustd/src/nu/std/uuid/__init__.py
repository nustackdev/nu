"""Nu surface for Python's ``uuid`` module.

Mirrors ``uuid`` 1-1: ``UUID`` is the class (a Form), ``uuid1``/``uuid3``/
``uuid4``/``uuid5`` are the module-level functions. Three layers behind it:
``forms`` (the class), ``functions`` (the free functions), ``interactions``
(the atoms both build). Import it the way you would the stdlib::

    from nu.std.uuid import UUID, uuid4
    import nu.std.uuid as uuid     # then uuid.uuid4(), uuid.UUID.from_str(...)
"""

from __future__ import annotations

from nu.std.uuid.forms import UUID
from nu.std.uuid.functions import uuid1, uuid3, uuid4, uuid5


__all__ = ["UUID", "uuid1", "uuid3", "uuid4", "uuid5"]
