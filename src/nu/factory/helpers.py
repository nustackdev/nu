"""Internal helpers shared across factory builders.

Nothing user-facing here - just the base-kind allowlist / rejectlist that
``InteractionFactory`` (and the specialized wrappers around it) share.
"""

from __future__ import annotations

from nu.lang.kinds import (
    Command,
    Flow,
    Reduction,
    ScalarAction,
    ScalarQuery,
    Span,
    StreamAction,
    StreamQuery,
)


__all__ = ["_ALLOWED_BASES", "_REJECTED_BASES"]


_ALLOWED_BASES: tuple[type, ...] = (ScalarQuery, Command, ScalarAction)
_REJECTED_BASES: tuple[type, ...] = (StreamQuery, StreamAction, Reduction, Flow, Span)
