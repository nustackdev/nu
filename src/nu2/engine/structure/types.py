"""Type aliases used across the structure module."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["RuleFn"]


type RuleFn = Callable[..., object]
"""The signature of an attribute rule.

Computed attributes (``Synthesized``, ``Inherited``) carry rules that the
compiler invokes during the attribute sweeps. The argument shape is
flavor-specific; see ``Synthesized`` and ``Inherited`` for the contracts.
"""
