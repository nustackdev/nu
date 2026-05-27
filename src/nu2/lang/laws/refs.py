"""Ref invariants: how Refs may sit in a Nu program.

Most Ref constraints are covered by the composition matrix; this module
hosts what the matrix can't express (a Ref as a Nu program's root atom is
not a program in the observable sense).

Currently empty; the dimension agent fills it (``ref_not_root``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu2.engine import Law


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = ()
