"""Nu surface for Python's ``functools``.

Only ``reduce`` is modeled: it is the one ``functools`` member that is a runtime
value operation (a fold over a stream). The rest are out of Nu's value model and
intentionally absent:

- ``partial`` / ``partialmethod`` / ``cmp_to_key`` produce *callables* - Nu has
  no first-class function value at the user surface.
- ``lru_cache`` / ``cache`` / ``cached_property`` are *stateful* (memoization) -
  they need the effect model (not yet built).
- ``wraps`` / ``update_wrapper`` / ``total_ordering`` are decorators over Python
  metadata, not runtime operations.

Import like the stdlib::

    from nu.std.functools import reduce
"""

from __future__ import annotations

from nu.std.functools.functions import reduce


__all__ = ["reduce"]
