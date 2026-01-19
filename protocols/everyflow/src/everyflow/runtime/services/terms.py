"""Service for managing terms execution (bridge for EveryShape Terms)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from ._base import ServiceBase


if TYPE_CHECKING:
    from pv.loc import path
    from everyterm.term import Context, Ref, Term


__all__ = ["TermsService"]


@attrs.frozen
class TermsService(ServiceBase):
    """Service for managing terms execution (bridge for EveryShape Terms)."""

    def execute_term[V](self, term: Term[V], ctx: Context | None = None) -> V:
        """Execute an EveryShape Term.

        Uses passed storage context if available, otherwise creates appropriate context
        (snapshot for reads, transaction for writes).
        """
        if ctx is None:
            with self.storage.context(read_only=False) as ctx:
                return term.execute(ctx)
        else:
            return term.execute(ctx)

    def resolve_ref(self, ref: Ref, ctx: Context | None = None) -> path.Path:
        """Resolve Ref to its value.

        Uses passed storage context if available, otherwise creates snapshot context
        """
        if ctx is None:
            with self.storage.context(read_only=True) as ctx:
                return ref.resolve(ctx)
        else:
            return ref.resolve(ctx)
