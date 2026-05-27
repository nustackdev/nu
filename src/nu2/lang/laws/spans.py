"""Span transparency laws: a Span wraps a body and forwards its yield.

A Span has a body; the Span's declared body cardinality matches the body's
resolved cardinality. Most Span constraints follow from the composition
matrix walk treating Span as transparent; this module hosts what's left.

Currently empty; the dimension agent fills it
(``span_has_body``, ``span_cardinality_matches_body``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu2.engine import Law


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = ()
