"""Nu surface for Python's ``uuid`` module.

Mirrors ``uuid`` 1-1: ``UUID`` is the class (a Form), ``uuid1``/``uuid3``/
``uuid4``/``uuid5`` are the module-level functions. Three layers behind it:
``forms`` (the class), ``functions`` (the free functions), ``interactions``
(the atoms both build). Import it the way you would the stdlib::

    from nustd.uuid import UUID, uuid4
    import nustd.uuid as uuid     # then uuid.uuid4(), uuid.UUID.from_str(...)

The leaves that hold these values in a Shape slot sit one submodule per
fabric: ``nustd.uuid.mem`` for ``nu.mem``, loaded with this package, and
``nustd.uuid.kv`` for ``nustd.kv``, imported by its own path.
"""

from __future__ import annotations

from nustd.uuid import mem
from nustd.uuid.forms import UUID
from nustd.uuid.functions import uuid1, uuid3, uuid4, uuid5


__all__ = ["UUID", "mem", "uuid1", "uuid3", "uuid4", "uuid5"]
