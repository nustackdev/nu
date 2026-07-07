"""The services axis of the Context fabric: typed bindings for execution resources.

A service is a typed binding on the Context (``ctx.bind(SolanaClient, client)``).
``ServiceRef`` names it; the read is the dual role (self-yield the bound
service). Existence check is ``ServiceExistsQuery``. Method dispatch
(``MethodFactory`` + ``method_action`` / ``method_command`` / ``method_query``)
lives in ``nu.factory`` because it works for any receiver, not only a
bound service.
"""

from __future__ import annotations

from .queries import ServiceExistsQuery
from .refs import ServiceRef


__all__ = ["ServiceExistsQuery", "ServiceRef"]
