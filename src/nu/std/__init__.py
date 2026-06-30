"""Nu standard library - typed Nu surfaces for Python's standard library.

Each submodule mirrors a Python stdlib module by name (``uuid``, ``datetime``,
``decimal`` ...). Import through the submodule, the way you would the stdlib
itself - there is no shortcut re-export off ``nu.std``::

    from nu.std.uuid import UUID, uuid4
    import nu.std.uuid as uuid

A value type is a **Form** - the typed access surface you call methods on. Its
operations are **interactions**: reused from ``nu.core`` where they already
exist (comparison, attribute reads, casts) or added alongside the Form as new
atoms where core can't express them (e.g. constructors). No opaque ``FuncCall``
escape hatch - every op is a first-class term.
"""

from __future__ import annotations
