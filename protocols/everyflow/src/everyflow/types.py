"""Type definitions for EveryFlow."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyterm.shape import RValue, Term

    from .flow import Flow
    from .runtime import Runtime


__all__ = [
    "Condition",
    "Executable",
]


type Executable = "Flow | Term"
type Condition = "RValue | bool | Callable[[Runtime], bool]"
