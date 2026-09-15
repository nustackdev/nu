"""Nu surface for Python's ``pathlib`` module - pure path operations only.

Mirrors ``pathlib`` 1-1: ``Path`` is the class (a Form), backed by ``PurePath``
so only the lexical operations that never touch the filesystem are modeled.
``pathlib`` has no module-level functions, so there are just two layers:
``forms`` (the class) and ``interactions`` (the constructor and method atoms;
property reads use core ``GetAttr``, comparison uses the core atoms).
Import it like the stdlib::

    from nustd.pathlib import Path
    import nustd.pathlib as pathlib    # pathlib.Path.of("a", "b"), ...
"""

from __future__ import annotations

from nustd.pathlib.forms import Path


__all__ = ["Path"]
