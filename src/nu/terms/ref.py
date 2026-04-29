"""Ref - address atom. Symbol + Nu atom (dual role).

A Ref names a location. It also acts as a Nu atom: when used as a child
in another Nu, it self-yields its value. See
projects/nu/model/02-atoms/01-ref.md.

Ref's `own_effects` is empty by class-time validator. Effects on a Ref
edge come from the parent atom; the dual-role construction-time READ
fires when a Ref binds into any non-Ref-only, non-body slot.
"""

from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar

from .nu import NuBase, register_subclass_validator
from .types import Realization


__all__ = ["Ref"]


T = TypeVar("T")


class Ref(NuBase, Generic[T]):
    """Address atom. Concrete subclasses pin the fabric.

    `realization = SCALAR` - reading a Ref produces a single value (the
    materialized value at the address) or EMPTY. Concrete subclasses
    override `eval` / `aeval` with the actual resolution path.
    """

    own_effects: ClassVar[dict[int, Any]] = {}
    realization: ClassVar[Realization] = Realization.SCALAR

    def eval(self, ctx: Any) -> T:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.eval not implemented"
        raise NotImplementedError(msg)

    async def aeval(self, ctx: Any) -> T:  # noqa: ANN401, D102
        msg = f"{type(self).__name__}.aeval not implemented"
        raise NotImplementedError(msg)


def _validate_ref(cls: type) -> None:
    """Ref subclasses must keep `own_effects` empty."""
    own = getattr(cls, "own_effects", {})
    if own:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Ref subclasses must "
            f"declare empty `own_effects` (got {own!r}). Effects on a Ref "
            "come from the parent atom, not from the Ref class."
        )
        raise TypeError(msg)


register_subclass_validator(Ref, _validate_ref)
