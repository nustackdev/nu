"""Observability laws: a Nu program must mutate Context to be meaningful.

A program with no WRITE anywhere in its subtree is non-observable - it
runs and returns, but Context is unchanged. Whether to reject or warn is a
design call kept open in the model doc; this module hosts the wiring.

Currently empty; the dimension agent fills it (``program_mutates``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu2.engine import Law


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = ()
