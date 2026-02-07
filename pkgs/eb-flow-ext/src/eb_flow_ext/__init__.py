"""eb_flow_ext -- Flow extensions and tree meta-transforms.

Cancellation:
    CancelledError            -- exception raised on cancellation
    CheckCancellation         -- leaf flow checking a Var[bool]
    add_cancellation_checks   -- tree transform inserting checks in loops

Progress:
    Progress                  -- lifecycle tracking wrapper
    add_progress              -- tree transform wrapping flows

Logging:
    Log                       -- structured logging flow
    Debug                     -- debug print flow
"""

from __future__ import annotations

from .cancellation import CancelledError, CheckCancellation, add_cancellation_checks
from .logging import Debug, Log
from .progress import Progress, add_progress


__all__ = [
    "CancelledError",
    "CheckCancellation",
    "Debug",
    "Log",
    "Progress",
    "add_cancellation_checks",
    "add_progress",
]
