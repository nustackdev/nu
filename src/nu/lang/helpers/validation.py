"""Nu-specialized validate: binds the Nu LAWS.

Wraps ``nu.engine.validate`` with Nu's law set so callers don't have to
pass them. Returns the same Program for chaining.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import validate as _validate

from .. import LAWS


if TYPE_CHECKING:
    from nu.engine.compilation import Program


def validate(program: Program) -> Program:
    """Validate a compiled Program against the Nu law set."""
    _validate(program, *LAWS)
    return program
