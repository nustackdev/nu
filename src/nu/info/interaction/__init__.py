"""The interaction kind: guide, record, assembler, checker.

Four files, one per verb the kind specializes. ``guide`` says what must be
written, ``record`` is what comes out, ``parse`` assembles it and ``validate``
checks it. The sibling packages for Form, Ref, Shape and Service follow the
same four, each owning its own record.
"""

from __future__ import annotations

from nu.info.interaction.guide import GUIDE
from nu.info.interaction.parse import catalogue, parse_interaction
from nu.info.interaction.record import InteractionRecord
from nu.info.interaction.validate import unpacked_arity, validate_interaction


__all__ = [
    "GUIDE",
    "InteractionRecord",
    "catalogue",
    "parse_interaction",
    "unpacked_arity",
    "validate_interaction",
]
