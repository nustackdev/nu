"""json interactions - one factory binding per host call.

Core can't parse or serialize JSON, so ``loads`` and ``dumps`` are new atoms
bound straight to the stdlib callables. They go through ``InteractionFactory``
rather than the ``host`` sugar so type-checkers see a ``ScalarQuery`` class
(``host`` is annotated to return ``object``). Keyword options (``indent``,
``sort_keys``, ...) ride as keyword children, so a computed value works as
well as a constant.

Both bindings are pure and deterministic (``dumps`` keeps dict order, so the
same input gives the same text), so a future constant-folding pass may fold
them freely.
"""

from __future__ import annotations

import json

from nu.factory import InteractionFactory
from nu.lang.kinds import ScalarQuery


__all__ = [
    "JsonDumps",
    "JsonLoads",
]


JsonLoads = InteractionFactory(ScalarQuery, "JsonLoads", json.loads)
JsonDumps = InteractionFactory(ScalarQuery, "JsonDumps", json.dumps)
