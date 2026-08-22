"""Nu-specialized compile: binds the finalized Nu SCHEMA.

Wraps ``nu.engine.compile`` with Nu's schema so callers don't have to
pass it. The engine's ``Program.__init__`` already stashes the schema on
the returned Program as ``_schema`` for downstream round-trips.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import compile as _compile

from .. import SCHEMA


if TYPE_CHECKING:
    from nu.engine.compilation import Program
    from nu.engine.structure import Term


def compile(term: Term) -> Program:
    """Compile a Nu Term against the Nu schema; return a runnable Program."""
    return _compile(term, SCHEMA)
